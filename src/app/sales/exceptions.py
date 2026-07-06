class RangoFechasInvalidoError(Exception):
    def __init__(self):
        super().__init__(
            "La fecha de inicio no puede ser posterior a la fecha fin")
