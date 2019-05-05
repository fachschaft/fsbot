class RocketClientException(Exception):
    """This expection is raised if there is any problem with the
    DDP Client
    """
    pass


class RocketBotException(Exception):
    """General rocketbot exception
    """
    pass


class RocketBotPollException(RocketBotException):
    """Exception for the poll module
    """
    pass
