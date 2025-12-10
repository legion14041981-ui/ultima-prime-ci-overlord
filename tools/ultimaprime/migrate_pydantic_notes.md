# Pydantic v1 → v2 Migration Notes

## Key Changes for ULTIMA-PRIME Auto-Patching

### 1. Field Validator Changes

**v1 (Old):**
```python
from pydantic import BaseModel, Field

class User(BaseModel):
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    name: str = Field(..., max_length=100)
```

**v2 (New):**
```python
from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator

class User(BaseModel):
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    name: str = Field(..., max_length=100)
```

**Auto-patch regex → pattern:**
- Search: `Field\([^)]*regex=`
- Replace: `Field(..., pattern=` (context-aware)

### 2. Validator Decorator

**v1:**
```python
from pydantic import validator

class Model(BaseModel):
    value: int
    
    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('must be positive')
        return v
```

**v2:**
```python
from pydantic import field_validator

class Model(BaseModel):
    value: int
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('must be positive')
        return v
```

### 3. Config Class → model_config

**v1:**
```python
class Model(BaseModel):
    value: str
    
    class Config:
        arbitrary_types_allowed = True
```

**v2:**
```python
from pydantic import ConfigDict

class Model(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    value: str
```

### 4. Import Changes

| v1 | v2 |
|----|----|    
| `from pydantic import validator` | `from pydantic import field_validator` |
| `from pydantic import root_validator` | `from pydantic import model_validator` |
| `from pydantic import parse_obj` | Use `.model_validate()` |
| `from pydantic.json import pydantic_encoder` | Use `.model_dump_json()` |

## ULTIMA-PRIME Patching Strategy

1. **Scan Phase**: Detect v1-only patterns in source
2. **Generate Phase**: Create diff-based patches
3. **Review Phase**: Human review of changes
4. **Apply Phase**: Commit to draft PR

### Files to Review After Migration
- Any file with `@validator`
- Any file with `Field(..., regex=`
- Any file with `class Config:`
- Any file with `parse_obj()` or `json()`

## Testing After Migration

```bash
# Install Pydantic v2
pip install 'pydantic>=2.0'

# Run tests
pytest -v

# Check for remaining v1 imports
git grep -n "from pydantic import validator" -- '*.py'
```
