@router.post("/users", status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    current_admin: User = Depends(get_current_admin_user),  # из зависимости
    user_service: UserService = Depends(get_user_service)
):
    """Создание нового пользователя (только админ)"""
    new_user = await user_service.create_user(user_data.username, user_data.password, user_data.role, user_data.projects)
    # Логирование действия админа
    admin_logger.info(f"Admin {current_admin.username} created user {new_user.username}")
    return {"id": new_user.id, "username": new_user.username}
