#!/usr/bin/env python3
"""
Database Manager Module

Railway PostgreSQL database management module
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Railway PostgreSQL database management"""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            # 개발 환경용 기본값
            self.database_url = "postgresql://localhost:5432/rag_tutor"
            logger.warning("DATABASE_URL not found, using default local database")
        
        self._init_tables()
    
    def get_connection(self):
        """DB 연결 생성"""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
    
    # database_manager.py 파일에서 _init_tables 함수를 이 코드로 교체하세요.

    def _init_tables(self):
        """테이블 초기화"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # 사용자 테이블
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            session_id VARCHAR(255) UNIQUE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # 문서 테이블
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS documents (
                            id SERIAL PRIMARY KEY,
                            user_session_id VARCHAR(255) NOT NULL,
                            original_filename VARCHAR(255) NOT NULL,
                            display_name VARCHAR(255) NOT NULL,
                            file_hash VARCHAR(64) UNIQUE NOT NULL,
                            file_path VARCHAR(500) NOT NULL,
                            file_size INTEGER NOT NULL,
                            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            status VARCHAR(50) DEFAULT 'uploaded',
                            indexed BOOLEAN DEFAULT false
                        );
                    """)
                    
                    # 인덱스 메타데이터 테이블 
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS document_indexes (
                            id SERIAL PRIMARY KEY,
                            user_session_id VARCHAR(255) NOT NULL,
                            index_path VARCHAR(500) NOT NULL,
                            document_count INTEGER NOT NULL,
                            file_hashes JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_active BOOLEAN DEFAULT true
                        );
                    """)
                    
                    # 대화 히스토리 테이블 
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS conversations (
                            id SERIAL PRIMARY KEY,
                            user_session_id VARCHAR(255) NOT NULL,
                            user_message TEXT NOT NULL,
                            tutor_response TEXT NOT NULL,
                            context_used TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # 인덱스 생성
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_documents_session 
                        ON documents(user_session_id);
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_conversations_session 
                        ON conversations(user_session_id);
                    """)
                    
                    conn.commit()
                    logger.info("Database tables initialized successfully")
                    
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # 개발 환경에서는 SQLite로 fallback 가능
            if "localhost" in str(self.database_url):
                logger.info("Falling back to file-based storage for development")
    
    def create_or_get_user(self, session_id: str) -> Dict:
        """사용자 생성 또는 조회"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # 기존 사용자 확인
                    cur.execute(
                        "SELECT * FROM users WHERE session_id = %s",
                        (session_id,)
                    )
                    user = cur.fetchone()
                    
                    if not user:
                        # 새 사용자 생성
                        cur.execute(
                            "INSERT INTO users (session_id) VALUES (%s) RETURNING *",
                            (session_id,)
                        )
                        user = cur.fetchone()
                        conn.commit()
                        logger.info(f"New user created: {session_id}")
                    else:
                        # 마지막 활동 시간 업데이트
                        cur.execute(
                            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE session_id = %s",
                            (session_id,)
                        )
                        conn.commit()
                    
                    return dict(user)
                    
        except Exception as e:
            logger.error(f"User creation/retrieval failed: {e}")
            # Fallback: 기본 사용자 정보 반환
            return {
                'id': 0,
                'session_id': session_id,
                'created_at': datetime.now(),
                'last_active': datetime.now()
            }
    
    def save_uploaded_document(self, session_id: str, file_info: Dict) -> int:
        """업로드된 문서 정보 저장"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO documents 
                        (user_session_id, original_filename, display_name, file_hash, 
                         file_path, file_size, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        session_id,
                        file_info['original_filename'],
                        file_info['display_name'],
                        file_info['file_hash'],
                        file_info['file_path'],
                        file_info['file_size'],
                        'uploaded'
                    ))
                    doc_id = cur.fetchone()['id']
                    conn.commit()
                    logger.info(f"Document saved: {file_info['display_name']} (ID: {doc_id})")
                    return doc_id
                    
        except Exception as e:
            logger.error(f"Document save failed: {e}")
            return -1
    
    def get_user_documents(self, session_id: str) -> List[Dict]:
        """사용자의 문서 목록 조회"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM documents 
                        WHERE user_session_id = %s 
                        ORDER BY upload_date DESC
                    """, (session_id,))
                    documents = [dict(row) for row in cur.fetchall()]
                    logger.info(f"Retrieved {len(documents)} documents for session {session_id}")
                    return documents
                    
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []
    
    def mark_documents_indexed(self, session_id: str, index_path: str, file_hashes: List[str]) -> bool:
        """문서들을 인덱싱됨으로 표시"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # 기존 인덱스 비활성화
                    cur.execute("""
                        UPDATE document_indexes 
                        SET is_active = false 
                        WHERE user_session_id = %s
                    """, (session_id,))
                    
                    # 문서 상태 업데이트
                    cur.execute("""
                        UPDATE documents 
                        SET status = 'indexed', indexed = true 
                        WHERE user_session_id = %s AND status = 'uploaded'
                    """, (session_id,))
                    
                    doc_count = cur.rowcount
                    
                    # 새 인덱스 메타데이터 저장
                    cur.execute("""
                        INSERT INTO document_indexes 
                        (user_session_id, index_path, document_count, file_hashes)
                        VALUES (%s, %s, %s, %s)
                    """, (session_id, index_path, doc_count, json.dumps(file_hashes)))
                    
                    conn.commit()
                    logger.info(f"Marked {doc_count} documents as indexed for session {session_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Index marking failed: {e}")
            return False
    
    def get_active_index(self, session_id: str) -> Optional[Dict]:
        """사용자의 활성 인덱스 정보 조회"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM document_indexes 
                        WHERE user_session_id = %s AND is_active = true
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """, (session_id,))
                    index_info = cur.fetchone()
                    return dict(index_info) if index_info else None
                    
        except Exception as e:
            logger.error(f"Active index retrieval failed: {e}")
            return None
    
    def save_conversation(self, session_id: str, user_message: str, tutor_response: str, context_used: str = "") -> bool:
        """대화 히스토리 저장"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO conversations 
                        (user_session_id, user_message, tutor_response, context_used)
                        VALUES (%s, %s, %s, %s)
                    """, (session_id, user_message, tutor_response, context_used))
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Conversation save failed: {e}")
            return False
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """대화 히스토리 조회"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM conversations 
                        WHERE user_session_id = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (session_id, limit))
                    conversations = [dict(row) for row in cur.fetchall()]
                    return list(reversed(conversations))  # 시간순 정렬
                    
        except Exception as e:
            logger.error(f"Conversation history retrieval failed: {e}")
            return []
    
    def cleanup_old_data(self, days_old: int = 30):
        """오래된 데이터 정리"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # 오래된 사용자와 관련 데이터 삭제
                    cur.execute("""
                        DELETE FROM conversations 
                        WHERE created_at < NOW() - INTERVAL '%s days'
                    """, (days_old,))
                    
                    cur.execute("""
                        DELETE FROM documents 
                        WHERE upload_date < NOW() - INTERVAL '%s days'
                    """, (days_old,))
                    
                    cur.execute("""
                        DELETE FROM users 
                        WHERE last_active < NOW() - INTERVAL '%s days'
                    """, (days_old,))
                    
                    conn.commit()
                    logger.info(f"Cleaned up data older than {days_old} days")
                    
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")

    def calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"File hash calculation failed: {e}")
            return str(hash(file_path))  # Fallback

        
    def get_index_by_id(self, index_id: int) -> Optional[Dict]:
        """인덱스 ID로 인덱스 정보 조회"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM document_indexes 
                        WHERE id = %s
                    """, (index_id,))
                    index_info = cur.fetchone()
                    return dict(index_info) if index_info else None
                    
        except Exception as e:
            logger.error(f"Index retrieval by ID failed: {e}")
            return None
    
    def find_indexes_by_file_hash(self, hashes: List[str]) -> List[Dict]:
        """
        lookup indexes by file hashes
        Args:
            hashes: List of file hashes to search for
        Returns:
            List[Dict]: List of index metadata dictionaries matching the hashes
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM document_indexes 
                        WHERE file_hashes @> %s::jsonb
                    """, (json.dumps(hashes),))
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            logger.error(f"Index retrieval by file hash failed: {e}")
            return []