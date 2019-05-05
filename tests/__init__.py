import logging

# Configure logging
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(name)s]: %(message)s', "%Y-%m-%d %H:%M:%S"))
root = logging.getLogger()
root.handlers.clear()
root.addHandler(console)

# Configure logglevels
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("rocketbot").setLevel(logging.DEBUG)
logging.getLogger("tests").setLevel(logging.DEBUG)
