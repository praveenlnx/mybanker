CREATE TABLE `users` (`name` varchar(25) NOT NULL, `isadmin` enum('yes','no') NOT NULL, `password` varchar(40) NOT NULL, `email` varchar(50) DEFAULT NULL, PRIMARY KEY (`name`))
INSERT INTO `users` VALUES ('admin','yes','*AC95DDE0D45FA2A466E4BF7378A6E8EB8D20F35','')
