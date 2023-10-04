import importlib

# Name of the module to import
module_name = 'app'  # Replace with the actual module name

# Import the module
my_module = importlib.import_module(module_name)

# Access the Flask app and routes defined in the module
app = my_module.app

# You can now run the Flask app as you normally would
if __name__ == '__main__':
    app.run()
