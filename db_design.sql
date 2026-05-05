-- ==========================================
-- 少数民族音乐App 核心数据表创建脚本 (MySQL 8.0)
-- 引擎: InnoDB
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
-- ==========================================

-- 设置客户端连接字符集为utf8mb4
SET NAMES utf8mb4;

-- ==========================================
-- 1. 删除已存在的表，解除外键依赖约束，方便重复执行
-- ==========================================
DROP TABLE IF EXISTS `records`;    -- 演唱记录表（存在外键依赖，必须先删）
DROP TABLE IF EXISTS `music_dict`; -- 少数民族音乐字典表
DROP TABLE IF EXISTS `users`;      -- 用户信息表

-- ==========================================
-- 2. 创建核心表
-- ==========================================

-- 2.1 创建 users 表（用户信息表）
CREATE TABLE `users` (
    `id` BIGINT AUTO_INCREMENT COMMENT '自增主键id',
    `phone` CHAR(11) NOT NULL COMMENT '手机号（11位字符）',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '加密密码',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间/创建时间',
    PRIMARY KEY (`id`) COMMENT '主键索引',
    UNIQUE KEY `uk_phone` (`phone`) COMMENT '高频查询：手机号唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户信息表';

-- 2.2 创建 music_dict 表（少数民族音乐字典表）
CREATE TABLE `music_dict` (
    `id` BIGINT AUTO_INCREMENT COMMENT '自增主键id',
    `nation` VARCHAR(50) NOT NULL COMMENT '民族名称',
    `song_name` VARCHAR(100) NOT NULL COMMENT '歌名',
    `video_url` TEXT COMMENT '视频URL地址',
    `temperament_tags` JSON COMMENT '气质标签（JSON类型，支持多标签）',
    `science_copy` TEXT COMMENT '科普文案内容',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`) COMMENT '主键索引',
    KEY `idx_nation` (`nation`) COMMENT '高频查询：民族普通索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='少数民族音乐字典表';

-- 2.3 创建 records 表（演唱记录与评分表）
CREATE TABLE `records` (
    `id` BIGINT AUTO_INCREMENT COMMENT '自增主键id',
    `user_id` BIGINT NOT NULL COMMENT '关联用户ID',
    `music_id` BIGINT NOT NULL COMMENT '关联音乐ID',
    `total_score` DECIMAL(5,2) DEFAULT '0.00' COMMENT '总分（0-100范围）',
    `pitch_score` DECIMAL(5,2) DEFAULT '0.00' COMMENT '音准分',
    `emotion_score` DECIMAL(5,2) DEFAULT '0.00' COMMENT '情感分',
    `ai_comment` TEXT COMMENT 'AI评语',
    `record_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`) COMMENT '主键索引',
    CONSTRAINT `fk_records_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_records_music_id` FOREIGN KEY (`music_id`) REFERENCES `music_dict` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `chk_total_score` CHECK (`total_score` >= 1 AND `total_score` <= 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='演唱记录与评分表';

-- ==========================================
-- 3. 插入示例测试数据 (基于图片中的10首云南少数民族民歌)
-- ==========================================

-- 3.1 插入 users 表测试数据
INSERT INTO `users` (`phone`, `password_hash`) VALUES
('13800138001', '$2a$10$hashedpassword1234567890'), -- 模拟加密密码
('13800138002', '$2a$10$hashedpassword2345678901'),
('13800138003', '$2a$10$hashedpassword3456789012');

-- 3.2 插入 music_dict 表数据 (与图片中的10首歌和metadata.py的ID完全对应)
INSERT INTO `music_dict` (`id`, `nation`, `song_name`, `video_url`, `temperament_tags`, `science_copy`) VALUES
(1, '彝族', '阿老表', 'https://example.com/videos/1.mp4', '["浑厚", "旷达", "穿透力强", "粗犷"]', '《阿老表》是滇中彝区经典欢聚对唱歌谣，常伴随左脚舞传唱，旋律高亢明亮，是彝乡烟火气与豪爽性格的生动代表。'),
(2, '哈尼族', '其多列', 'https://example.com/videos/2.mp4', '["清亮", "灵动", "轻快", "甜美"]', '《其多列》是哈尼族流传最广的儿童歌谣，旋律清脆活泼，描绘了哈尼孩童山野嬉戏的场景，充满童真与生命力。'),
(3, '彝族', '海菜腔', 'https://example.com/videos/3.mp4', '["高亢", "嘹亮", "气息绵长", "粗犷"]', '海菜腔是彝族四大腔之一，发源于红河沿岸，以气息绵长、旋律婉转著称，被誉为“东方咏叹调”，是国家级非物质文化遗产。'),
(4, '白族', '蝴蝶泉边', 'https://example.com/videos/4.mp4', '["柔美", "婉转", "清甜", "甜美"]', '《蝴蝶泉边》是白族经典对唱情歌，取材于蝴蝶泉传说，旋律温婉流畅，生动展现了白族青年男女的纯真爱情与大理风花雪月的意境。'),
(5, '傣族', '月光下的凤尾竹', 'https://example.com/videos/5.mp4', '["轻柔", "甜美", "细腻", "甜美"]', '葫芦丝是傣族、阿昌族等民族的传统乐器，音色轻柔细腻，被誉为“东方萨克斯”，《月光下的凤尾竹》更是描绘了傣家竹楼月夜的浪漫意境。'),
(6, '傈僳族', '放羊调', 'https://example.com/videos/6.mp4', '["质朴", "嘹亮", "略带山野粗粝感", "粗犷"]', '《放羊调》是傈僳族原生态山歌，源于日常放牧生活，旋律粗犷接地气，充满山野间的自由气息，是傈僳族人民生活与情感的真实写照。'),
(7, '佤族', '加林赛', 'https://example.com/videos/7.mp4', '["粗犷", "奔放", "爆发力强", "粗犷"]', '《加林赛》是佤族传统歌舞曲，常用于木鼓节等盛大庆典，节奏强劲、情绪激昂，是佤族人民豪迈奔放、热情好客的性格体现。'),
(8, '藏族', '香格里拉', 'https://example.com/videos/8.mp4', '["高亢", "辽阔", "共鸣饱满", "粗犷"]', '《香格里拉》以滇西北藏区为背景，旋律辽阔通透，充满雪域高原的神圣感，唱出了人们对香格里拉这片世外桃源的向往与赞美。'),
(9, '拉祜族', '快乐拉祜', 'https://example.com/videos/9.mp4', '["欢快", "明亮", "富有律动感", "甜美"]', '《快乐拉祜》是拉祜族代表性歌曲，旋律活泼喜庆，展现了拉祜族人民安居乐业、载歌载舞的幸福生活，是拉祜文化的生动符号。'),
(10, '纳西族', '纳西三部曲', 'https://example.com/videos/10.mp4', '["古朴", "醇厚", "沉稳", "粗犷"]', '《纳西三部曲》融合了纳西族传统民歌与东巴文化元素，旋律沉稳醇厚，承载着纳西族的历史记忆与人文底蕴，是纳西族音乐文化的集大成者。');

-- 3.3 插入 records 表测试数据
INSERT INTO `records` (`user_id`, `music_id`, `total_score`, `pitch_score`, `emotion_score`, `ai_comment`) VALUES
(1, 1, 95.50, 96.00, 95.00, '太地道了！一开口就像站在彝家山岗上，声音透亮又有穿透力，把《阿老表》的热情豪迈全唱活了，听着就想跟着跳左脚舞！'),
(2, 2, 88.00, 85.50, 90.50, '声音清亮又灵动，把哈尼族童谣的俏皮感唱出来了！就是个别段落有点抢拍，再放松一点会更有童趣~'),
(3, 3, 92.00, 90.00, 94.00, '音色嘹亮又有张力，把彝族高腔的气势唱出来了！就是个别转音有点生硬，再柔一点会更有韵味~');

-- ==========================================
-- 4. 验证查询（用于校验结构和数据）
-- ==========================================
-- 可以在客户端取消注释运行以下代码来验证
/*
SELECT * FROM `users`;
SELECT * FROM `music_dict`;
SELECT * FROM `records`;

-- 联合查询示例，获取用户的演唱记录及歌曲详情
SELECT 
    u.phone AS '用户手机', 
    m.nation AS '民族', 
    m.song_name AS '歌曲名', 
    r.total_score AS '演唱得分', 
    r.ai_comment AS 'AI点评'
FROM `records` r
JOIN `users` u ON r.user_id = u.id
JOIN `music_dict` m ON r.music_id = m.id;
*/
