CREATE TABLE `users` (`name` varchar(50) NOT NULL, `username` varchar(25) NOT NULL, `isadmin` enum('yes','no') NOT NULL, `password` varchar(100) NOT NULL, `email` varchar(50) DEFAULT NULL, PRIMARY KEY (`name`))
INSERT INTO `users` VALUES ('MyBanker Admin', 'admin', 'yes','5607df723a0b7e4b36f2d61091e883c7c856196796fdc1ff13800920a24e3f9d','')
