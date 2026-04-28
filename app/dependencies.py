async def get_current_user(authorization: str = Header(...), token_service: TokenService = Depends(get_token_service)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401)
    token = authorization[7:]
    payload = token_service.decode_token(token, "access")
    if not payload:
        raise HTTPException(401)
    return payload  # dict с user_id, projects, role
