from typing import Dict, List, Any, Optional, Set
import ast
import os
import re
from pathlib import Path
import json

class CodeRelationshipMapper:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.relationship_cache = {}
    
    async def analyze_file_dependencies(self, file_path: str, project_root: str) -> Dict[str, Any]:
        """Analyze dependencies for a specific file"""
        if not os.path.exists(file_path):
            return {"dependencies": [], "dependents": [], "impact_score": 0}
        
        dependencies = set()
        
        # Parse file based on extension
        if file_path.endswith('.py'):
            dependencies.update(self._parse_python_imports(file_path))
        elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            dependencies.update(self._parse_js_imports(file_path))
        elif file_path.endswith('.java'):
            dependencies.update(self._parse_java_imports(file_path))
        
        # Find dependents (files that import this one)
        dependents = await self._find_dependents(file_path, project_root)
        
        # Calculate impact score
        impact_score = len(dependents) * 2 + len(dependencies)
        
        return {
            "file_path": file_path,
            "dependencies": list(dependencies),
            "dependents": dependents,
            "impact_score": impact_score,
            "risk_level": self._calculate_risk_level(impact_score)
        }
    
    def _parse_python_imports(self, file_path: str) -> Set[str]:
        """Parse Python imports"""
        dependencies = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.add(node.module)
        except:
            # Fallback to regex parsing
            dependencies.update(self._regex_parse_imports(file_path, r'(?:from\s+(\S+)\s+import|import\s+(\S+))'))
        
        return dependencies
    
    def _parse_js_imports(self, file_path: str) -> Set[str]:
        """Parse JavaScript/TypeScript imports"""
        patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
            r'import\([\'"]([^\'"]+)[\'"]\)'
        ]
        
        dependencies = set()
        for pattern in patterns:
            dependencies.update(self._regex_parse_imports(file_path, pattern))
        
        return dependencies
    
    def _parse_java_imports(self, file_path: str) -> Set[str]:
        """Parse Java imports"""
        return self._regex_parse_imports(file_path, r'import\s+([^;]+);')
    
    def _regex_parse_imports(self, file_path: str, pattern: str) -> Set[str]:
        """Generic regex-based import parsing"""
        dependencies = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            matches = re.finditer(pattern, content)
            for match in matches:
                # Get the first non-None group
                for group in match.groups():
                    if group:
                        dependencies.add(group.strip())
                        break
        except:
            pass
        
        return dependencies
    
    async def _find_dependents(self, target_file: str, project_root: str) -> List[str]:
        """Find files that depend on the target file"""
        dependents = []
        target_module = self._file_to_module_name(target_file, project_root)
        
        # Search through project files
        for root, dirs, files in os.walk(project_root):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.java')):
                    file_path = os.path.join(root, file)
                    if file_path != target_file:
                        if await self._file_imports_target(file_path, target_module, target_file):
                            dependents.append(file_path)
        
        return dependents
    
    def _file_to_module_name(self, file_path: str, project_root: str) -> str:
        """Convert file path to module name"""
        rel_path = os.path.relpath(file_path, project_root)
        module_name = rel_path.replace(os.sep, '.').replace('.py', '').replace('.js', '').replace('.ts', '')
        return module_name
    
    async def _file_imports_target(self, file_path: str, target_module: str, target_file: str) -> bool:
        """Check if file imports the target"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for various import patterns
            patterns = [
                target_module,
                os.path.basename(target_file).replace('.py', '').replace('.js', '').replace('.ts', ''),
                os.path.relpath(target_file, os.path.dirname(file_path))
            ]
            
            for pattern in patterns:
                if pattern in content:
                    return True
                    
        except:
            pass
        
        return False
    
    def _calculate_risk_level(self, impact_score: int) -> str:
        """Calculate risk level based on impact score"""
        if impact_score > 20:
            return "high"
        elif impact_score > 10:
            return "medium"
        else:
            return "low"
    
    async def forecast_change_impact(self, file_path: str, project_root: str) -> Dict[str, Any]:
        """Forecast the impact of changing a file"""
        analysis = await self.analyze_file_dependencies(file_path, project_root)
        
        # Get test coverage for affected files
        coverage_info = await self._get_test_coverage(analysis['dependents'], project_root)
        
        # Calculate downstream impact
        downstream_modules = set()
        for dependent in analysis['dependents']:
            dep_analysis = await self.analyze_file_dependencies(dependent, project_root)
            downstream_modules.update(dep_analysis['dependents'])
        
        return {
            "direct_impact": {
                "affected_files": analysis['dependents'],
                "count": len(analysis['dependents'])
            },
            "downstream_impact": {
                "affected_modules": list(downstream_modules),
                "count": len(downstream_modules)
            },
            "test_coverage": coverage_info,
            "risk_assessment": {
                "level": analysis['risk_level'],
                "score": analysis['impact_score'],
                "recommendation": self._get_change_recommendation(analysis)
            }
        }
    
    async def _get_test_coverage(self, file_paths: List[str], project_root: str) -> Dict[str, Any]:
        """Get test coverage information for files"""
        # This is a simplified version - would integrate with actual coverage tools
        total_files = len(file_paths)
        covered_files = 0
        
        for file_path in file_paths:
            # Look for corresponding test files
            test_patterns = [
                file_path.replace('.py', '_test.py'),
                file_path.replace('.py', '.test.py'),
                file_path.replace('.js', '.test.js'),
                file_path.replace('.ts', '.test.ts'),
                os.path.join(os.path.dirname(file_path), 'test_' + os.path.basename(file_path))
            ]
            
            for test_pattern in test_patterns:
                if os.path.exists(test_pattern):
                    covered_files += 1
                    break
        
        coverage_percentage = (covered_files / total_files * 100) if total_files > 0 else 100
        
        return {
            "total_files": total_files,
            "covered_files": covered_files,
            "coverage_percentage": round(coverage_percentage, 1),
            "coverage_gaps": [f for f in file_paths if not any(os.path.exists(p) for p in [
                f.replace('.py', '_test.py'),
                f.replace('.py', '.test.py'),
                f.replace('.js', '.test.js'),
                f.replace('.ts', '.test.ts')
            ])]
        }
    
    def _get_change_recommendation(self, analysis: Dict[str, Any]) -> str:
        """Get recommendation based on impact analysis"""
        impact_score = analysis['impact_score']
        dependents_count = len(analysis['dependents'])
        
        if impact_score > 20:
            return "High-impact change. Consider feature flags and staged rollout."
        elif impact_score > 10:
            return "Medium-impact change. Ensure comprehensive testing of dependent modules."
        elif dependents_count > 5:
            return "Multiple dependents detected. Run integration tests before merge."
        else:
            return "Low-impact change. Standard testing should suffice."
    
    async def store_relationship_graph(self, session_id: str, project_root: str):
        """Store the complete relationship graph for a project"""
        async with self.db_pool.acquire() as conn:
            # Clear existing relationships for this session
            await conn.execute("""
                DELETE FROM code_relationships WHERE session_id = $1
            """, session_id)
            
            # Scan project and store relationships
            for root, dirs, files in os.walk(project_root):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.java')):
                        file_path = os.path.join(root, file)
                        analysis = await self.analyze_file_dependencies(file_path, project_root)
                        
                        # Store relationships
                        await conn.execute("""
                            INSERT INTO code_relationships (
                                session_id, file_path, dependencies, dependents, 
                                impact_score, risk_level, created_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """, 
                            session_id, file_path, 
                            json.dumps(analysis['dependencies']),
                            json.dumps(analysis['dependents']),
                            analysis['impact_score'],
                            analysis['risk_level'],
                            datetime.utcnow()
                        )