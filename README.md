**Домашняя работа №5**

***В unittest добавил ещё пару тестов, которых изначально не было в предыдущей ДЗ (опционально):***  
test_additional_invalid_score_request  
test_additional_invalid_interests_request  

***Сами же модульные (unit) тесты реализованы с помощью pytest, где:***  
Симулируем попадание в кэш;  
Симулируем промах по кэшу (должен быть вызван метод cache_set);  
Симулируем исключение при обращении к хранилищу (должен всё равно вычислить score без выброса исключения).  

Создан CI для удобства проверки ДЗ :)
