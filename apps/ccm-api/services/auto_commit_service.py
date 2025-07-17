from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import json
import subprocess
import os

class AutoCommitService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.error_patterns = {
            'syntax': ['SyntaxError', 'syntax error', 'unexpected token'],
            'runtime': ['RuntimeError', 'NullPointerException', 'TypeError'],
            'auth': ['Authentication', 'Unauthorized', 'login', 'token'],
            'security': ['security', 'vulnerable', 'csrf', 'xss'],
            'performance': ['slow', 'timeout', 'memory', 'performance'],
            'test': ['test', 'spec', 'assert', 'expect'],
            'ui': ['css', 'style', 'component', 'render'],
            'api': ['api', 'endpoint', 'request', 'response'],
            'database': ['database', 'query', 'migration', 'sql']
        }
    
    async def detect_fix_completion(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Detect when a fix has been completed"""
        async with self.db_pool.acquire() as conn:
            # Look for recent test success after failures
            recent_tests = await conn.fetch("""
                SELECT encrypted_payload, timestamp
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type = 'test_run'
                AND timestamp >= NOW() - INTERVAL '10 minutes'
                ORDER BY timestamp DESC
                LIMIT 5
            """, session_id)
            
            if len(recent_tests) < 2:
                return None
            
            # Check if latest test passed after previous failures
            latest_test = recent_tests[0]
            try:
                latest_payload = json.loads(latest_test['encrypted_payload'])
                if latest_payload.get('status') == 'passed':
                    # Check if there were previous failures
                    for test in recent_tests[1:]:
                        test_payload = json.loads(test['encrypted_payload'])
                        if test_payload.get('status') == 'failed':
                            return {
                                "fix_detected": True,
                                "fix_time": latest_test['timestamp'],
                                "test_context": latest_payload
                            }
            except:
                pass
        
        return None
    
    async def generate_commit_message(self, session_id: str, repo_path: str) -> str:
        """Generate intelligent commit message"""
        # Get recent context
        async with self.db_pool.acquire() as conn:
            context_nodes = await conn.fetch("""
                SELECT agent, event_type, encrypted_payload, file_path, timestamp
                FROM context_nodes
                WHERE session_id = $1 
                AND timestamp >= NOW() - INTERVAL '30 minutes'
                ORDER BY timestamp DESC
                LIMIT 20
            """, session_id)
        
        # Analyze context for commit message
        analysis = await self._analyze_change_context(context_nodes, repo_path)
        
        # Generate structured commit message
        message_parts = []
        
        # Main action
        if analysis['error_type']:
            message_parts.append(f"Fix {analysis['error_type']} issue")
        elif analysis['feature_type']:
            message_parts.append(f"Add {analysis['feature_type']} feature")
        else:
            message_parts.append("Update code")
        
        # File context
        if analysis['primary_file']:
            file_name = os.path.basename(analysis['primary_file'])
            message_parts.append(f"in {file_name}")
        
        # Additional context
        if analysis['test_added']:
            message_parts.append("| Adds tests")
        
        if analysis['security_related']:
            message_parts.append("| Security improvement")
        
        # Tags
        tags = []
        if analysis['context_tags']:
            tags.extend(analysis['context_tags'])
        
        message = " ".join(message_parts)
        
        if tags:
            message += f" | Context: {'+'.join(tags)}"
        
        # Add issue reference if detected
        if analysis['issue_ref']:
            message += f" | Relates to {analysis['issue_ref']}"
        
        return message
    
    async def _analyze_change_context(self, context_nodes: List, repo_path: str) -> Dict[str, Any]:
        """Analyze context to understand what changed"""
        analysis = {
            'error_type': None,
            'feature_type': None,
            'primary_file': None,
            'test_added': False,
            'security_related': False,
            'context_tags': [],
            'issue_ref': None
        }
        
        # Find most edited file
        file_edits = {}
        error_messages = []
        
        for node in context_nodes:
            try:
                payload = json.loads(node['encrypted_payload'])
                
                # Count file edits
                if node['file_path'] and node['event_type'] == 'file_modified':
                    file_edits[node['file_path']] = file_edits.get(node['file_path'], 0) + 1
                
                # Collect error messages
                if 'error' in payload or node['event_type'] in ['test_failed', 'error_occurred']:
                    error_text = str(payload).lower()
                    error_messages.append(error_text)
                
                # Check for test files
                if node['file_path'] and ('test' in node['file_path'] or 'spec' in node['file_path']):
                    analysis['test_added'] = True
                
                # Look for issue references
                issue_match = re.search(r'(PROJ-\d+|#\d+|JIRA-\d+)', str(payload))
                if issue_match:
                    analysis['issue_ref'] = issue_match.group(1)
                    
            except:
                continue
        
        # Determine primary file
        if file_edits:
            analysis['primary_file'] = max(file_edits, key=file_edits.get)
        
        # Classify error type
        all_errors = ' '.join(error_messages)
        for error_type, patterns in self.error_patterns.items():
            if any(pattern in all_errors for pattern in patterns):
                analysis['error_type'] = error_type
                analysis['context_tags'].append(error_type)
                break
        
        # Check for security-related changes
        security_keywords = ['auth', 'password', 'token', 'security', 'crypto']
        if any(keyword in all_errors for keyword in security_keywords):
            analysis['security_related'] = True
        
        return analysis
    
    async def auto_commit_if_appropriate(self, session_id: str, repo_path: str) -> Optional[str]:
        """Automatically commit if fix is detected and appropriate"""
        fix_detection = await self.detect_fix_completion(session_id)
        
        if not fix_detection:
            return None
        
        # Check if auto-commit is enabled for this session
        auto_commit_enabled = await self._check_auto_commit_enabled(session_id)
        if not auto_commit_enabled:
            return None
        
        try:
            # Generate commit message
            commit_message = await self.generate_commit_message(session_id, repo_path)
            
            # Stage changes
            subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
            
            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Log the commit
            await self._log_auto_commit(session_id, commit_message, result.stdout)
            
            return commit_message
            
        except subprocess.CalledProcessError as e:
            # Log error but don't raise
            print(f"Auto-commit failed: {e}")
            return None
    
    async def _check_auto_commit_enabled(self, session_id: str) -> bool:
        """Check if auto-commit is enabled for session"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT auto_commit_enabled FROM user_preferences 
                WHERE session_id = $1
            """, session_id)
            
            # Default to False if no preference set
            return result if result is not None else False
    
    async def _log_auto_commit(self, session_id: str, message: str, output: str):
        """Log auto-commit action"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO context_nodes (
                    session_id, agent, event_type, encrypted_payload, timestamp
                ) VALUES ($1, 'git', 'auto_commit', $2, $3)
            """, session_id, json.dumps({
                "commit_message": message,
                "git_output": output,
                "auto_generated": True
            }), datetime.utcnow())
    
    async def suggest_commit_message(self, session_id: str, repo_path: str) -> Dict[str, Any]:
        """Suggest commit message without auto-committing"""
        message = await self.generate_commit_message(session_id, repo_path)
        
        # Get additional context for the suggestion
        async with self.db_pool.acquire() as conn:
            recent_changes = await conn.fetch("""
                SELECT file_path, COUNT(*) as edit_count
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type = 'file_modified'
                AND timestamp >= NOW() - INTERVAL '30 minutes'
                GROUP BY file_path
                ORDER BY edit_count DESC
                LIMIT 5
            """, session_id)
        
        return {
            "suggested_message": message,
            "confidence": 0.8,  # Could be enhanced with ML
            "files_changed": [row['file_path'] for row in recent_changes],
            "auto_stage_recommended": len(recent_changes) <= 3
        }