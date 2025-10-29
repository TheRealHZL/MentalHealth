"""
Database Configuration

PostgreSQL Setup mit SQLAlchemy, Alembic Migrations und Connection Management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.pool import NullPool
import logging
from typing import AsyncGenerator

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database metadata with naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

# Async engine for PostgreSQL
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    pool_size=10,
    max_overflow=20,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True
)

async def init_database():
    """Initialize database - create tables if they don't exist"""
    
    try:
        logger.info("🗃️ Initializing PostgreSQL database...")
        
        # Import all models to ensure they're registered
        from src.models import ALL_MODELS
        
        # Test connection
        async with async_engine.begin() as conn:
            # Create tables (in production, use Alembic migrations instead)
            if settings.ENVIRONMENT == "development":
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Database tables created/verified")
            else:
                # In production, just test the connection
                await conn.execute("SELECT 1")
                logger.info("✅ Database connection verified")
        
        logger.info("🎉 PostgreSQL database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

async def close_database():
    """Close database connections"""
    
    try:
        logger.info("🔌 Closing database connections...")
        await async_engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session"""
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_session():
    """Get synchronous session for migrations"""
    
    from sqlalchemy.orm import sessionmaker
    
    SyncSessionLocal = sessionmaker(
        bind=sync_engine,
        autocommit=False,
        autoflush=False
    )
    
    return SyncSessionLocal()

# Database health check
async def check_database_health() -> dict:
    """Check database connection health"""
    
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute("SELECT version(), current_database(), current_user")
            row = result.fetchone()
            
            return {
                "status": "healthy",
                "database": row[1],
                "user": row[2],
                "version": row[0],
                "connection_pool": {
                    "size": async_engine.pool.size(),
                    "checked_in": async_engine.pool.checkedin(),
                    "checked_out": async_engine.pool.checkedout(),
                    "overflow": async_engine.pool.overflow(),
                    "invalid": async_engine.pool.invalid()
                }
            }
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Database utilities
class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    async def create_backup(backup_name: str = None) -> str:
        """Create database backup (requires pg_dump)"""
        
        import subprocess
        from datetime import datetime
        
        if not backup_name:
            backup_name = f"mindbridge_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        try:
            # Extract connection details
            db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            
            # Run pg_dump
            result = subprocess.run([
                "pg_dump",
                db_url,
                "-f", f"backups/{backup_name}",
                "--no-password",
                "--verbose"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Database backup created: {backup_name}")
                return backup_name
            else:
                logger.error(f"❌ Backup failed: {result.stderr}")
                raise Exception(f"Backup failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Backup error: {e}")
            raise
    
    @staticmethod
    async def vacuum_analyze():
        """Run VACUUM ANALYZE on all tables"""
        
        try:
            async with async_engine.begin() as conn:
                await conn.execute("VACUUM ANALYZE")
                logger.info("✅ Database vacuum analyze completed")
        except Exception as e:
            logger.error(f"❌ Vacuum analyze failed: {e}")
            raise
    
    @staticmethod
    async def get_table_sizes() -> dict:
        """Get size information for all tables"""
        
        try:
            async with async_engine.begin() as conn:
                result = await conn.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)
                
                tables = []
                for row in result.fetchall():
                    tables.append({
                        "schema": row[0],
                        "table": row[1], 
                        "size": row[2],
                        "size_bytes": row[3]
                    })
                
                return {"tables": tables}
                
        except Exception as e:
            logger.error(f"❌ Failed to get table sizes: {e}")
            return {"error": str(e)}

# Database monitoring
class DatabaseMetrics:
    """Database metrics collection"""
    
    @staticmethod
    async def get_connection_stats() -> dict:
        """Get connection pool statistics"""
        
        return {
            "pool_size": async_engine.pool.size(),
            "checked_in": async_engine.pool.checkedin(),
            "checked_out": async_engine.pool.checkedout(),
            "overflow": async_engine.pool.overflow(),
            "invalid": async_engine.pool.invalid()
        }
    
    @staticmethod
    async def get_query_stats() -> dict:
        """Get query performance statistics"""
        
        try:
            async with async_engine.begin() as conn:
                result = await conn.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements 
                    ORDER BY total_time DESC 
                    LIMIT 10
                """)
                
                queries = []
                for row in result.fetchall():
                    queries.append({
                        "query": row[0][:100] + "..." if len(row[0]) > 100 else row[0],
                        "calls": row[1],
                        "total_time": row[2],
                        "mean_time": row[3],
                        "rows": row[4]
                    })
                
                return {"top_queries": queries}
                
        except Exception as e:
            # pg_stat_statements might not be installed
            return {"error": "pg_stat_statements not available"}
