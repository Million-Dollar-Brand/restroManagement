# Changes Made by OpenCode

**Date:** May 04, 2026

## Bug Fix: SQLAlchemy "Can't operate on closed transaction inside context manager"

### File Modified
- `app/api/v1/endpoints/super_admin.py`

### Problem
The `create_restaurant` endpoint was throwing a SQLAlchemy transaction error: **"Can't operate on closed transaction inside context manager"**.

The root cause was improper transaction management across nested function calls:

1. **`create_postgres_schema()` (line 56)** - Called `await session.commit()` inside a function that was invoked within an outer `async with session.begin():` block. This committed and closed the transaction prematurely, causing the outer context manager to fail when it tried to commit again on exit.

2. **`create_tenant_tables()` (line 124)** - Had its own nested `async with session.begin():` block, which conflicted with the outer transaction manager in `create_restaurant()`.

3. **Cleanup block (line 243)** - Attempted to use `async with session.begin():` after the main transaction block had already exited, potentially operating on a closed or invalid session.

### Changes Made

#### 1. `create_postgres_schema()` - Removed premature commit
**Before:**
```python
async def create_postgres_schema(schema_name: str, session: AsyncSession) -> None:
    try:
        await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        await session.commit()  # <-- PROBLEM: Closes transaction inside outer begin()
    except Exception as e:
        await session.rollback()
        raise HTTPException(...)
```

**After:**
```python
async def create_postgres_schema(schema_name: str, session: AsyncSession) -> None:
    try:
        await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        # Commit is now handled by the outer session.begin() context manager
    except Exception as e:
        raise HTTPException(...)
        # Rollback is now handled by the outer session.begin() context manager
```

#### 2. `create_tenant_tables()` - Removed nested transaction block
**Before:**
```python
async def create_tenant_tables(schema_name: str, session: AsyncSession) -> None:
    try:
        await set_search_path(session, schema_name)
        async with session.begin():  # <-- PROBLEM: Nested begin() conflicts with outer
            await session.run_sync(TenantBase.metadata.create_all)
    except Exception as e:
        await session.rollback()
        raise HTTPException(...)
    finally:
        await set_search_path(session, "public")
```

**After:**
```python
async def create_tenant_tables(schema_name: str, session: AsyncSession) -> None:
    try:
        await set_search_path(session, schema_name)
        await session.run_sync(TenantBase.metadata.create_all)
        await set_search_path(session, "public")
    except Exception as e:
        await set_search_path(session, "public")
        raise HTTPException(...)
```

#### 3. Cleanup block - Direct session operations instead of nested begin()
**Before:**
```python
except Exception as e:
    try:
        async with session.begin():  # <-- PROBLEM: May fail if session is closed
            await session.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
    except:
        pass
```

**After:**
```python
except Exception as e:
    try:
        await session.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
        await session.commit()
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
```

### Key Principles Applied

1. **Single transaction owner**: When using `async with session.begin():`, only that context manager should control commit/rollback. Helper functions should NOT call `commit()` or `rollback()`.

2. **No nested `session.begin()`**: Avoid nesting `async with session.begin():` blocks. Let the outermost transaction manager handle the lifecycle.

3. **Session state awareness**: After a `session.begin()` context manager exits (especially on exception), the session may be in a closed or rolled-back state. Subsequent operations need to handle this gracefully.

### Session Management Pattern to Follow

```python
@router.post("/endpoint")
async def my_endpoint(session: AsyncSession = Depends(get_db)):
    async with session.begin():
        # All DB operations here
        # Do NOT call session.commit() or session.rollback() in helper functions
        await helper_function(session)
        session.add(model)
    # Transaction auto-commits on successful exit
    # Transaction auto-rolls back on exception
```

### Notes for Future Development

- The `get_db()` dependency in `app/database.py` correctly yields a session and ensures cleanup in its `finally` block
- Endpoints using `get_tenant_session()` also work correctly since they don't wrap operations in additional `session.begin()` blocks
- Other endpoints (`staff.py`, `menu.py`, `orders.py`) use direct `await session.commit()` calls which is correct since they are NOT wrapped in `async with session.begin():` blocks
