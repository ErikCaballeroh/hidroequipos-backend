class UserNotFoundError(Exception):
    def __init__(self, user_uuid: str):
        self.user_uuid = user_uuid
        super().__init__(f"Usuario {user_uuid} no encontrado")


class UsernameAlreadyExistsError(Exception):
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"Usuario {username} ya registrado")


class InvalidCredentialsError(Exception):
    def __init__(self):
        super().__init__("Usuario o contraseña inválidos")


class BranchNotFoundError(Exception):
    def __init__(self, branch_id: str):
        self.branch_id = branch_id
        super().__init__(f"Sucursal {branch_id} no encontrada")
