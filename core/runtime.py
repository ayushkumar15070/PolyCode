
import json


class Runtime:
    def __init__(self):
        self.variables = {}

    def set_variable(self, name, value):
        self.variables[name] = value

    def get_variable(self, name):
        return self.variables.get(name)

    def get_all_variables(self):
        return self.variables.copy()

    def load_variables(self, variables):
        self.variables.update(variables)

    def serialize(self):
        return json.dumps(self.variables)

    def clear(self):
        self.variables.clear()
