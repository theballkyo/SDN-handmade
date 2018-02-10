import enum


@enum.unique
class FlowState(enum.Enum):
    ERROR = -1

    IDLE = 0
    # When create flow
    WAIT_FOR_PROCESS = 1
    # When submit flow
    PROCESSING = 2

    # Rollback
    WAIT_FOR_ROLLBACK = 10
    ROLLBACK = 11


@enum.unique
class FlowActionState(enum.Enum):
    # Flow was processed
    IDLE = 0
    # When create flow
    WAIT_FOR_PROCESS = 1
    # When submit flow
    PROCESSING = 2

    # Rollback
    WAIT_FOR_ROLLBACK = 10
    ROLLBACK = 11
