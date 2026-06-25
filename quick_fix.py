import os
os.chdir(r"C:\Users\Administrator\WorkBuddy\Claw\evolution")
with open("core\engine_v3. py", "r") as f: c = f.read()
# Fix CycleResult
c = c.replace('class CycleResult:\n    def __init__(self, cycle_ id: int, phase: str, status: str, errors: int = 0):\n        self.cycle_id = cycle_id\n        self.phase = phase\n        self.status = status\n        self. errors = errors', 'class CycleResult:\n    def __init__(self, cycle_ id: int, phase: str, status: str, errors: int = 0, improvements: int = 0, skills_created: int = 0, message: str = "", timestamp: str = "", success: bool = True):\n        self.cycle_id = cycle_id\n        self.phase = phase\n        self.status = status\n        self.errors = errors\n        self.improvements = improvements\n        self.skills_created = skills_created\n        self.message = message\n        self.timestamp = timestamp\n        self.success = success\n    def to_dict(self) -> dict:\n        return {"cycle_id": self.cycle_id}') 
with open("core\engine. py", "w") as f: f.write(c)
print("Done")