class RocketClientException(Exception):
    """This expection is raised if there is any problem with the
    DDP Client
    """
    pass


class RocketCancelSubscription(Exception):
    """Raise this expection in a subscription callback function
    in order to cancle the subscription"""
    pass


class RocketBotException(Exception):
    """General rocketbot exception
    """
    pass