
from core.engine import PolyCodeEngine

code = """
@python
a = 10
b = 30

@cpp
int sum = a + b;

@javascript
console.log(sum);
"""

engine = PolyCodeEngine()
print(engine.run(code))
