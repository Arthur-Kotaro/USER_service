-- ============================================================
-- Очистка пользователей и их ролей
-- ============================================================

DELETE FROM users_roles;
DELETE FROM users;
ALTER SEQUENCE users_user_id_seq RESTART WITH 1;
