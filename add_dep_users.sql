-- ============================================================
-- 1. Очистка
-- ============================================================
DELETE FROM users_roles;
DELETE FROM users;
DELETE FROM department;
ALTER SEQUENCE users_user_id_seq RESTART WITH 1;

-- ============================================================
-- 2. Создание отделов
-- ============================================================
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
('IT', 'IT-отдел', NULL);

-- ============================================================
-- 3. Создание недостающих ролей
-- ============================================================
INSERT INTO roles (role_title, role_code) VALUES
('director', 'DIR'),
('upp_head', 'UPPH'),
('bureau_head', 'BURH'),
('storekeeper', 'STK'),
('proto_tech_bureau_head', 'PTBH')
ON CONFLICT (role_title) DO NOTHING;

-- ============================================================
-- 4. Добавление пользователей
-- ============================================================
INSERT INTO users (user_name, email, password_hash, dept_code, created_at, updated_at, password_updated_at) VALUES

-- Директор
('Красильников Николай Петрович', 'director@company.com', md5('LeaderPass456!'), 'DIR_TECH', NOW(), NOW(), NOW()),

-- Начальник УПП
('Родионов Андрей Владимирович', 'upp.head@company.com', md5('LeaderPass456!'), 'UPP', NOW(), NOW(), NOW()),

-- Менеджеры по индустриализации (2)
('Власова Елена Ивановна', 'ind.manager1@company.com', md5('LeaderPass456!'), 'DIR_TECH', NOW(), NOW(), NOW()),
('Кузнецов Дмитрий Сергеевич', 'ind.manager2@company.com', md5('LeaderPass456!'), 'DIR_TECH', NOW(), NOW(), NOW()),

-- Цех №1
('Колосов Дмитрий Иванович', 'shop1.head@company.com', md5('LeaderPass456!'), 'UPP_SHOP', NOW(), NOW(), NOW()),
('Маслов Игорь Петрович', 'master.shop1.1@shop.com', md5('TestPassword123!'), 'UPP_SHOP', NOW(), NOW(), NOW()),
('Соколов Денис Сергеевич', 'master.shop1.2@shop.com', md5('TestPassword123!'), 'UPP_SHOP', NOW(), NOW(), NOW()),
('Королев Николай Викторович', 'master.shop1.3@shop.com', md5('TestPassword123!'), 'UPP_SHOP', NOW(), NOW(), NOW()),
('Гришин Александр Владимирович', 'master.shop1.4@shop.com', md5('TestPassword123!'), 'UPP_SHOP', NOW(), NOW(), NOW()),

-- Цех №2
('Захаров Роман Олегович', 'shop2.head@company.com', md5('LeaderPass456!'), 'UPP_SHOP', NOW(), NOW(), NOW()),
('Авдеев Максим Александрович', 'master.shop2.1@shop.com', md5('TestPassword123!'), 'UPP_SHOP', NOW(), NOW(), NOW()),
('Рыбакова Наталья Валерьевна', 'master.shop2.2@shop.com', md5('TestPassword123!'), 'UPP_SHOP', NOW(), NOW(), NOW()),
('Семёнов Владислав Сергеевич', 'master.shop2.3@shop.com', md5('TestPassword123!'), 'UPP_SHOP', NOW(), NOW(), NOW()),
('Фролов Илья Васильевич', 'master.shop2.4@shop.com', md5('TestPassword123!'), 'UPP_SHOP', NOW(), NOW(), NOW()),

-- КТО
('Белоусов Павел Николаевич', 'kto.head@company.com', md5('LeaderPass456!'), 'UPP_KTO', NOW(), NOW(), NOW()),

-- Бюро №1
('Громов Сергей Алексеевич', 'bureau1.head@kto.com', md5('LeaderPass456!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Блинов Андрей Николаевич', 'technologist.1.1@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Карпова Ольга Владимировна', 'technologist.1.2@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Мартынов Илья Петрович', 'technologist.1.3@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Суханова Марина Юрьевна', 'technologist.1.4@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Филиппов Денис Евгеньевич', 'technologist.1.5@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),

-- Бюро №2
('Журавлёв Павел Сергеевич', 'bureau2.head@kto.com', md5('LeaderPass456!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Козловский Артём Иванович', 'technologist.2.1@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Лапшина Екатерина Дмитриевна', 'technologist.2.2@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Чистяков Максим Олегович', 'technologist.2.3@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Яковлева Анна Сергеевна', 'technologist.2.4@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Шульгин Виктор Николаевич', 'technologist.2.5@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),

-- Бюро №3
('Русаков Евгений Валерьевич', 'bureau3.head@kto.com', md5('LeaderPass456!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Агафонова Ирина Петровна', 'technologist.3.1@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Беспалов Сергей Николаевич', 'technologist.3.2@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Доронина Татьяна Викторовна', 'technologist.3.3@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Миронов Глеб Андреевич', 'technologist.3.4@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Овчинникова Юлия Олеговна', 'technologist.3.5@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),

-- Бюро №4
('Тимофеев Кирилл Александрович', 'bureau4.head@kto.com', md5('LeaderPass456!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Галкина Виктория Алексеевна', 'technologist.4.1@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Ефимов Сергей Викторович', 'technologist.4.2@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Калашникова Оксана Николаевна', 'technologist.4.3@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Орехов Антон Павлович', 'technologist.4.4@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Федяева Елена Валерьевна', 'technologist.4.5@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),

-- Проработчики (5)
('Ткаченко Олег Иванович', 'proctech.1@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Потапова Светлана Андреевна', 'proctech.2@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Никифоров Дмитрий Сергеевич', 'proctech.3@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Субботина Наталья Викторовна', 'proctech.4@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),
('Кузьмин Владислав Павлович', 'proctech.5@kto.com', md5('TestPassword123!'), 'UPP_KTO', NOW(), NOW(), NOW()),

-- Руководители проектов (8)
('Лебедев Андрей Владимирович', 'pm.proto.1@upp.com', md5('TestPassword123!'), 'UPP', NOW(), NOW(), NOW()),
('Комаров Николай Сергеевич', 'pm.proto.2@upp.com', md5('TestPassword123!'), 'UPP', NOW(), NOW(), NOW()),
('Куликова Татьяна Михайловна', 'pm.proto.3@upp.com', md5('TestPassword123!'), 'UPP', NOW(), NOW(), NOW()),
('Богданов Егор Васильевич', 'pm.proto.4@upp.com', md5('TestPassword123!'), 'UPP', NOW(), NOW(), NOW()),
('Мухина Ольга Владимировна', 'pm.proto.5@upp.com', md5('TestPassword123!'), 'UPP', NOW(), NOW(), NOW()),
('Карпов Денис Юрьевич', 'pm.proto.6@upp.com', md5('TestPassword123!'), 'UPP', NOW(), NOW(), NOW()),
('Савельева Ирина Александровна', 'pm.proto.7@upp.com', md5('TestPassword123!'), 'UPP', NOW(), NOW(), NOW()),
('Никольский Алексей Петрович', 'pm.proto.8@upp.com', md5('TestPassword123!'), 'UPP', NOW(), NOW(), NOW()),

-- ОГК
('Смирнов Александр Владимирович', 'chief_engineer@ogk.com', md5('LeaderPass456!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),

-- Архитекторы (5)
('Константинов Андрей Валерьевич', 'arch.1@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Леонова Мария Геннадьевна', 'arch.2@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Медведев Сергей Васильевич', 'arch.3@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Пономарев Александр Игоревич', 'arch.4@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Розова Оксана Сергеевна', 'arch.5@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),

-- IST (5)
('Соловьев Владислав Николаевич', 'ist.1@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Крылова Елена Павловна', 'ist.2@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Морозов Денис Викторович', 'ist.3@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Григорьев Денис Павлович', 'ist.4@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Фролова Екатерина Игоревна', 'ist.5@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),

-- PFE (5)
('Никифорова Анна Владимировна', 'pfe.1@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Тарасов Илья Николаевич', 'pfe.2@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Фомина Татьяна Сергеевна', 'pfe.3@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Шишкин Алексей Петрович', 'pfe.4@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),
('Захарова Ольга Сергеевна', 'pfe.5@ogk.com', md5('TestPassword123!'), 'EXTERNAL_OGK', NOW(), NOW(), NOW()),

-- Бюро закупок
('Ильин Алексей Викторович', 'purchase.head@bureau.com', md5('LeaderPass456!'), 'BUREAU_PURCHASE', NOW(), NOW(), NOW()),
('Киселева Татьяна Владимировна', 'purchase.1@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE', NOW(), NOW(), NOW()),
('Поляков Александр Сергеевич', 'purchase.2@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE', NOW(), NOW(), NOW()),
('Сорокина Ольга Владимировна', 'purchase.3@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE', NOW(), NOW(), NOW()),
('Беляев Роман Иванович', 'purchase.4@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE', NOW(), NOW(), NOW()),
('Андреев Антон Сергеевич', 'purchase.5@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE', NOW(), NOW(), NOW()),

-- Прототипный склад
('Максимов Денис Иванович', 'warehouse.head@bureau.com', md5('LeaderPass456!'), 'BUREAU_WAREHOUSE', NOW(), NOW(), NOW()),
('Орлова Елена Петровна', 'warehouse.1@bureau.com', md5('TestPassword123!'), 'BUREAU_WAREHOUSE', NOW(), NOW(), NOW()),
('Крылов Михаил Викторович', 'warehouse.2@bureau.com', md5('TestPassword123!'), 'BUREAU_WAREHOUSE', NOW(), NOW(), NOW()),
('Никитин Павел Геннадьевич', 'warehouse.3@bureau.com', md5('TestPassword123!'), 'BUREAU_WAREHOUSE', NOW(), NOW(), NOW()),
('Алексеев Владимир Сергеевич', 'warehouse.4@bureau.com', md5('TestPassword123!'), 'BUREAU_WAREHOUSE', NOW(), NOW(), NOW()),
('Борисова Екатерина Андреевна', 'warehouse.5@bureau.com', md5('TestPassword123!'), 'BUREAU_WAREHOUSE', NOW(), NOW(), NOW()),

-- Бюро серийной логистики
('Васильев Игорь Петрович', 'serial_log.head@bureau.com', md5('LeaderPass456!'), 'BUREAU_SERIAL_LOG', NOW(), NOW(), NOW()),
('Воробьев Илья Сергеевич', 'serial_log.1@bureau.com', md5('TestPassword123!'), 'BUREAU_SERIAL_LOG', NOW(), NOW(), NOW()),
('Ермолова Наталья Петровна', 'serial_log.2@bureau.com', md5('TestPassword123!'), 'BUREAU_SERIAL_LOG', NOW(), NOW(), NOW()),
('Исаев Константин Викторович', 'serial_log.3@bureau.com', md5('TestPassword123!'), 'BUREAU_SERIAL_LOG', NOW(), NOW(), NOW()),
('Савченко Виталий Николаевич', 'serial_log.4@bureau.com', md5('TestPassword123!'), 'BUREAU_SERIAL_LOG', NOW(), NOW(), NOW()),
('Ткачева Ирина Владимировна', 'serial_log.5@bureau.com', md5('TestPassword123!'), 'BUREAU_SERIAL_LOG', NOW(), NOW(), NOW()),

-- Бюро логистики покупных КИ
('Федоров Роман Олегович', 'purchase_log.head@bureau.com', md5('LeaderPass456!'), 'BUREAU_PURCHASE_LOG', NOW(), NOW(), NOW()),
('Федосеев Александр Сергеевич', 'purchase_log.1@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE_LOG', NOW(), NOW(), NOW()),
('Харитонова Елена Юрьевна', 'purchase_log.2@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE_LOG', NOW(), NOW(), NOW()),
('Цветков Владимир Петрович', 'purchase_log.3@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE_LOG', NOW(), NOW(), NOW()),
('Павлов Юрий Николаевич', 'purchase_log.4@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE_LOG', NOW(), NOW(), NOW()),
('Романова Оксана Викторовна', 'purchase_log.5@bureau.com', md5('TestPassword123!'), 'BUREAU_PURCHASE_LOG', NOW(), NOW(), NOW()),

-- Бюро межоперационной логистики
('Сергеев Иван Михайлович', 'interop_log.head@bureau.com', md5('LeaderPass456!'), 'BUREAU_INTEROP_LOG', NOW(), NOW(), NOW()),
('Козлова Ольга Сергеевна', 'interop_log.1@bureau.com', md5('TestPassword123!'), 'BUREAU_INTEROP_LOG', NOW(), NOW(), NOW()),
('Новиков Павел Андреевич', 'interop_log.2@bureau.com', md5('TestPassword123!'), 'BUREAU_INTEROP_LOG', NOW(), NOW(), NOW()),
('Морозова Ирина Викторовна', 'interop_log.3@bureau.com', md5('TestPassword123!'), 'BUREAU_INTEROP_LOG', NOW(), NOW(), NOW()),
('Волков Сергей Николаевич', 'interop_log.4@bureau.com', md5('TestPassword123!'), 'BUREAU_INTEROP_LOG', NOW(), NOW(), NOW()),
('Захарова Екатерина Петровна', 'interop_log.5@bureau.com', md5('TestPassword123!'), 'BUREAU_INTEROP_LOG', NOW(), NOW(), NOW()),

-- IT-отдел
('Сидорова Татьяна Ивановна', 'it.admin@company.com', md5('LeaderPass456!'), 'IT', NOW(), NOW(), NOW());

-- ============================================================
-- 5. Назначение ролей
-- ============================================================
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
