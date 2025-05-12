import pickle
import os

class StorageManager:
    def __init__(self, filename):
        self.filename = filename

    def save(self, data):
        try:
            with open(self.filename, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error al guardar estado: {e}")

    def load(self):
        if not os.path.exists(self.filename):
            return None
        try:
            with open(self.filename, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error al cargar estado: {e}")
            return None
