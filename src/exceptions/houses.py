class HouseError(Exception):
    pass


class HouseNotFound(HouseError):
    pass


class HouseAccessDenied(HouseError):
    pass


class HouseLoginAlreadyExists(HouseError):
    pass


class InvalidHouseCredentials(HouseError):
    pass


class AlreadyHouseParticipant(HouseError):
    pass


class ParticipantNotFound(HouseError):
    pass


class LastActiveAdmin(HouseError):
    pass


class InvalidParticipantTransition(HouseError):
    pass


class IncorrectHousePassword(HouseError):
    pass
