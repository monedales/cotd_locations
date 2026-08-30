class PipelineError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FrameReadError(PipelineError):
    pass


class InsufficientEventsError(PipelineError):
    pass


class MissingImageError(PipelineError):
    pass


class VideoDownloadError(PipelineError):
    pass


class SpotTableError(PipelineError):
    pass
