from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import asyncpg
from services.encryption_service import EncryptionService

class TemporalContextGraph:
    def __init__(self, db_pool, encryption_service: EncryptionService):
        self.db_pool = db_pool
        self.encryption = encryption_service
    
    async def store_context_node(self, session_id: str, node_data: Dict[str, Any]) -> str:
        """Store a context node in the temporal graph"""
        async with self.db_pool.acquire() as conn:
            # Encrypt sensitive data
            encrypted_payload = self.encryption.encrypt_context(node_data['payload'])
            
            node_id = await conn.fetchval("""
                INSERT INTO context_nodes (
                    session_id, agent, event_type, encrypted_payload, 
                    timestamp, file_path, line_number
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, 
                session_id, node_data['agent'], node_data['type'],
                encrypted_payload, datetime.fromisoformat(node_data['timestamp']),
                node_data.get('file_path'), node_data.get('line_number')
            )
            
            return str(node_id)
    
    async def create_relationship(self, from_node: str, to_node: str, 
                                 relationship_type: str, weight: float = 1.0):
        """Create relationships between context nodes"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO context_relationships (
                    from_node_id, to_node_id, relationship_type, weight, created_at
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (from_node_id, to_node_id, relationship_type) 
                DO UPDATE SET weight = $4, created_at = $5
            """, from_node, to_node, relationship_type, weight, datetime.utcnow())
    
    async def get_temporal_context(self, session_id: str, 
                                  time_window_minutes: int = 30) -> List[Dict]:
        """Get context within temporal window"""
        async with self.db_pool.acquire() as conn:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            rows = await conn.fetch("""
                SELECT cn.*, cr.relationship_type, cr.weight
                FROM context_nodes cn
                LEFT JOIN context_relationships cr ON cn.id = cr.from_node_id
                WHERE cn.session_id = $1 AND cn.timestamp >= $2
                ORDER BY cn.timestamp DESC
            """, session_id, cutoff_time)
            
            nodes = []
            for row in rows:
                try:
                    decrypted_payload = self.encryption.decrypt_context(row['encrypted_payload'])
                    nodes.append({
                        'id': row['id'],
                        'agent': row['agent'],
                        'type': row['event_type'],
                        'payload': decrypted_payload,
                        'timestamp': row['timestamp'].isoformat(),
                        'file_path': row['file_path'],
                        'relationship': row['relationship_type'],
                        'weight': row['weight']
                    })
                except Exception as e:
                    # Skip corrupted nodes
                    continue
            
            return nodes
    
    async def detect_patterns(self, session_id: str) -> Dict[str, Any]:
        """Detect behavioral patterns in context graph"""
        async with self.db_pool.acquire() as conn:
            # Detect looping behavior
            loops = await conn.fetch("""
                SELECT file_path, COUNT(*) as edit_count
                FROM context_nodes 
                WHERE session_id = $1 
                AND event_type = 'file_modified'
                AND timestamp >= NOW() - INTERVAL '20 minutes'
                GROUP BY file_path
                HAVING COUNT(*) > 3
            """, session_id)
            
            # Detect error patterns
            errors = await conn.fetch("""
                SELECT COUNT(*) as error_count
                FROM context_nodes 
                WHERE session_id = $1 
                AND (event_type = 'test_failed' OR encrypted_payload LIKE '%error%')
                AND timestamp >= NOW() - INTERVAL '10 minutes'
            """, session_id)
            
            return {
                'loops_detected': len(loops) > 0,
                'looping_files': [row['file_path'] for row in loops],
                'recent_errors': errors[0]['error_count'] if errors else 0,
                'pattern_score': min(len(loops) * 2 + (errors[0]['error_count'] if errors else 0), 10)
            }
    
    async def auto_wipe_old_data(self, hours: int = 24):
        """Auto-wipe data older than specified hours (ephemeral mode)"""
        async with self.db_pool.acquire() as conn:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Delete old relationships first (foreign key constraint)
            await conn.execute("""
                DELETE FROM context_relationships 
                WHERE created_at < $1
            """, cutoff_time)
            
            # Delete old nodes
            deleted_count = await conn.fetchval("""
                DELETE FROM context_nodes 
                WHERE timestamp < $1
                RETURNING COUNT(*)
            """, cutoff_time)
            
            return deleted_count