-- ============================================================
-- Пересоздание пользователей с правильными bcrypt-хешами
-- ============================================================

-- Очистка
DELETE FROM users_roles;
DELETE FROM users;
ALTER SEQUENCE users_user_id_seq RESTART WITH 1;

-- Отделы (если ещё нет)
INSERT INTO department (dept_code, dept_name, parent_dept_code) VALUES
('DIR_TECH', 'Дирекция технологов', NULL),
('UPP', 'УПП', 'DIR_TECH'),
('UPP_SHOP', 'УПП (цех)', 'UPP'),
('UPP_KTO', 'УПП (КТО)', 'UPP'),
('EXTERNAL_OGK', 'Внешний (ОГК)', NULL),
('BUREAU_PURCHASE', 'Бюро закупок', NULL),
('BUREAU_WAREHOUSE', 'Прототипный склад', NULL),
('BUREAU_SERIAL_LOG', 'Бюро серийной логистики', NULL),
('BUREAU_PURCHASE_LOG', 'Бюро логистики покупных КИ', NULL),
('BUREAU_INTEROP_LOG', 'Бюро межоперационной логистики', NULL),
('IT', 'IT-отдел', NULL)
ON CONFLICT (dept_code) DO NOTHING;

-- Роли
INSERT INTO roles (role_title, role_code) VALUES
('director', 'DIR'),
('upp_head', 'UPPH'),
('bureau_head', 'BURH'),
('storekeeper', 'STK'),
('proto_tech_bureau_head', 'PTBH')
ON CONFLICT (role_title) DO NOTHING;

-- Пользователи (подставь СВОИ хеши из шага 1!)
INSERT INTO users (user_name, email, password_hash, dept_code, created_at, updated_at, password_updated_at) VALUES

-- Руководители (LeaderPass456!)
('Красильников Николай Петрович', 'director@company.com', 
 '$2b$12$...', 'DIR_TECH', NOW(), NOW(), NOW()),

('Родионов Андрей Владимирович', 'upp.head@company.com', 
 '$2b$12$...', 'UPP', NOW(), NOW(), NOW()),

('Власова Елена Ивановна', 'ind.manager1@company.com', 
 '$2b$12$...', 'DIR_TECH', NOW(), NOW(), NOW()),

('Кузнецов Дмитрий Сергеевич', 'ind.manager2@company.com', 
 '$2b$12$...', 'DIR_TECH', NOW(), NOW(), NOW()),

('Колосов Дмитрий Иванович', 'shop1.head@company.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW()),

('Захаров Роман Олегович', 'shop2.head@company.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW()),

('Белоусов Павел Николаевич', 'kto.head@company.com', 
 '$2b$12$...', 'UPP_KTO', NOW(), NOW(), NOW()),

('Смирнов Александр Владимирович', 'chief_engineer@ogk.com', 
 '$2b$12$...', 'EXTERNAL_OGK', NOW(), NOW(), NOW()),

('Ильин Алексей Викторович', 'purchase.head@bureau.com', 
 '$2b$12$...', 'BUREAU_PURCHASE', NOW(), NOW(), NOW()),

('Максимов Денис Иванович', 'warehouse.head@bureau.com', 
 '$2b$12$...', 'BUREAU_WAREHOUSE', NOW(), NOW(), NOW()),

('Васильев Игорь Петрович', 'serial_log.head@bureau.com', 
 '$2b$12$...', 'BUREAU_SERIAL_LOG', NOW(), NOW(), NOW()),

('Федоров Роман Олегович', 'purchase_log.head@bureau.com', 
 '$2b$12$...', 'BUREAU_PURCHASE_LOG', NOW(), NOW(), NOW()),

('Сергеев Иван Михайлович', 'interop_log.head@bureau.com', 
 '$2b$12$...', 'BUREAU_INTEROP_LOG', NOW(), NOW(), NOW()),

('Сидорова Татьяна Ивановна', 'it.admin@company.com', 
 '$2b$12$...', 'IT', NOW(), NOW(), NOW());

-- Все остальные сотрудники (TestPassword123!)
INSERT INTO users (user_name, email, password_hash, dept_code, created_at, updated_at, password_updated_at) VALUES
('Маслов Игорь Петрович', 'master.shop1.1@shop.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW()),
('Соколов Денис Сергеевич', 'master.shop1.2@shop.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW()),
('Королев Николай Викторович', 'master.shop1.3@shop.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW()),
('Гришин Александр Владимирович', 'master.shop1.4@shop.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW()),

('Авдеев Максим Александрович', 'master.shop2.1@shop.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW()),
('Рыбакова Наталья Валерьевна', 'master.shop2.2@shop.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW()),
('Семёнов Владислав Сергеевич', 'master.shop2.3@shop.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW()),
('Фролов Илья Васильевич', 'master.shop2.4@shop.com', 
 '$2b$12$...', 'UPP_SHOP', NOW(), NOW(), NOW());

-- (Добавь сюда остальных сотрудников, если они есть в твоём списке)
-- ...

-- Назначение ролей
INSERT INTO users_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM users u, roles r
WHERE
    (u.email = 'director@company.com' AND r.role_title = 'director') OR
    (u.email = 'upp.head@company.com' AND r.role_title = 'upp_head') OR
    (u.email = 'ind.manager1@company.com' AND r.role_title = 'industrialization_manager') OR
    (u.email = 'ind.manager2@company.com' AND r.role_title = 'industrialization_manager') OR
    (u.email = 'shop1.head@company.com' AND r.role_title = 'shop_head') OR
    (u.email = 'shop2.head@company.com' AND r.role_title = 'shop_head') OR
    (u.email LIKE 'master.shop1.%' AND r.role_title = 'proto_master') OR
    (u.email LIKE 'master.shop2.%' AND r.role_title = 'proto_master') OR
    (u.email = 'kto.head@company.com' AND r.role_title = 'kto_head') OR
    (u.email LIKE 'bureau%.head@kto.com' AND r.role_title = 'proto_tech_bureau_head') OR
    (u.email LIKE 'technologist.%' AND r.role_title = 'proto_technologist') OR
    (u.email LIKE 'proctech.%' AND r.role_title = 'proctech') OR
    (u.email LIKE 'pm.proto.%' AND r.role_title = 'proto_pm') OR
    (u.email = 'chief_engineer@ogk.com' AND r.role_title = 'chief_engineer') OR
    (u.email LIKE 'arch.%@ogk.com' AND r.role_title = 'architect') OR
    (u.email LIKE 'ist.%@ogk.com' AND r.role_title = 'design_pm_senior') OR
    (u.email LIKE 'pfe.%@ogk.com' AND r.role_title = 'design_pm_junior') OR
    (u.email LIKE 'purchase.%' AND r.role_title = 'proto_purchaser') OR
    (u.email LIKE 'warehouse.%' AND r.role_title = 'storekeeper') OR
    (u.email LIKE 'serial_log.%' AND r.role_title = 'proto_logistician') OR
    (u.email LIKE 'purchase_log.%' AND r.role_title = 'proto_logistician') OR
    (u.email LIKE 'interop_log.%' AND r.role_title = 'proto_logistician') OR
    (u.email LIKE '%.head@bureau.com' AND r.role_title = 'bureau_head') OR
    (u.email = 'it.admin@company.com' AND r.role_title = 'admin')
ON CONFLICT DO NOTHING;
