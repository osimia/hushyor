# Hushyor API Documentation

Base URL: `http://127.0.0.1:8000/api/v1/` (dev) или `https://hushyor.com/api/v1/` (prod)

## Аутентификация

API использует JWT (JSON Web Tokens) для аутентификации. После успешного входа/регистрации вы получите `access_token` и `refresh_token`.

### Использование токена

Добавьте токен в заголовок запроса:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## Эндпоинты

### 🔐 Аутентификация

#### POST `/auth/register/`
Регистрация нового пользователя.

**Request Body:**
```json
{
  "username": "testuser",
  "password": "password123",
  "password2": "password123",
  "phone": "+992000000000",
  "full_name": "Иван Иванов",
  "email": "test@example.com"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Регистрация успешна",
  "user": {
    "id": 1,
    "username": "testuser",
    "first_name": "Иван",
    "last_name": "Иванов",
    "email": "test@example.com"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

#### POST `/auth/login/`
Вход пользователя.

**Request Body (по username):**
```json
{
  "username": "testuser",
  "password": "password123"
}
```

**Request Body (по телефону):**
```json
{
  "phone": "+992000000000",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Вход выполнен успешно",
  "user": {
    "id": 1,
    "username": "testuser",
    "first_name": "Иван",
    "last_name": "Иванов",
    "email": "test@example.com"
  },
  "profile": {
    "id": 1,
    "user": {...},
    "phone": "+992000000000",
    "streak": 5,
    "xp": 150
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

#### GET `/auth/profile/`
Получить профиль текущего пользователя. **Требует аутентификации.**

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "first_name": "Иван",
    "last_name": "Иванов",
    "email": "test@example.com"
  },
  "profile": {
    "id": 1,
    "phone": "+992000000000",
    "streak": 5,
    "xp": 150
  }
}
```

---

#### POST `/auth/token/refresh/`
Обновить access token используя refresh token.

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 🏠 Главная страница

#### GET `/home/`
Получить список всех предметов с прогрессом пользователя и статистикой.

**Response (200):**
```json
{
  "subjects": [
    {
      "id": 1,
      "title": "Математика",
      "icon": "🔢",
      "color": "#3B82F6",
      "total_tasks": 100,
      "completed_tasks": 25,
      "progress_percentage": 25
    },
    {
      "id": 5,
      "title": "Забони тоҷикӣ",
      "icon": "🇹🇯",
      "color": "#10B981",
      "total_tasks": 366,
      "completed_tasks": 0,
      "progress_percentage": 0
    }
  ],
  "stats": {
    "total_users": 150,
    "total_tasks": 1415,
    "total_subjects": 5
  }
}
```

---

### 📚 Предметы

#### GET `/subjects/`
Получить список всех предметов.

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Математика",
    "icon": "🔢",
    "color": "#3B82F6"
  }
]
```

---

#### GET `/subjects/{id}/`
Получить детальную информацию о предмете с темами. **Требует аутентификации для прогресса.**

**Response (200):**
```json
{
  "id": 1,
  "title": "Математика",
  "icon": "🔢",
  "color": "#3B82F6",
  "total_tasks": 100,
  "completed_tasks": 25,
  "progress_percentage": 25,
  "topics": [
    {
      "id": 1,
      "title": "Алгебра",
      "order": 1,
      "is_locked": false,
      "subject": 1,
      "total_tasks": 20,
      "completed_tasks": 5,
      "progress_percentage": 25
    }
  ]
}
```

---

### 📖 Темы

#### GET `/topics/`
Получить список всех тем.

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Алгебра",
    "order": 1,
    "is_locked": false,
    "subject": 1
  }
]
```

---

#### GET `/topics/{id}/`
Получить детальную информацию о теме.

**Response (200):**
```json
{
  "id": 1,
  "title": "Алгебра",
  "order": 1,
  "is_locked": false,
  "subject": 1,
  "total_tasks": 20,
  "completed_tasks": 5,
  "progress_percentage": 25
}
```

---

#### GET `/topics/{id}/tasks/`
Получить все задачи для конкретной темы.

**Response (200):**
```json
{
  "topic": {
    "id": 1,
    "title": "Алгебра",
    "total_tasks": 20,
    "completed_tasks": 5,
    "progress_percentage": 25
  },
  "tasks": [
    {
      "id": 1,
      "subject": 1,
      "subject_title": "Математика",
      "topic": 1,
      "topic_title": "Алгебра",
      "question": "Решите уравнение: 2x + 5 = 15",
      "options": {
        "1": "x = 5",
        "2": "x = 10",
        "3": "x = 7",
        "4": "x = 3"
      },
      "correct_answer": "1",
      "difficulty": 1,
      "order": 1,
      "is_solved": false,
      "attempts_count": 0
    }
  ]
}
```

---

### 📝 Задачи

#### GET `/tasks/`
Получить список всех задач (с пагинацией).

**Query Parameters:**
- `page` - номер страницы (по умолчанию 1)
- `page_size` - количество элементов на странице (по умолчанию 50)

**Response (200):**
```json
{
  "count": 1415,
  "next": "http://127.0.0.1:8000/api/v1/tasks/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "subject": 1,
      "topic": 1,
      "question": "Решите уравнение: 2x + 5 = 15",
      "options": {
        "1": "x = 5",
        "2": "x = 10",
        "3": "x = 7",
        "4": "x = 3"
      },
      "correct_answer": "1",
      "difficulty": 1,
      "order": 1
    }
  ]
}
```

---

#### GET `/tasks/{id}/`
Получить конкретную задачу. **Требует аутентификации для информации о попытках.**

**Response (200):**
```json
{
  "id": 1,
  "subject": 1,
  "subject_title": "Математика",
  "topic": 1,
  "topic_title": "Алгебра",
  "question": "Решите уравнение: 2x + 5 = 15",
  "options": {
    "1": "x = 5",
    "2": "x = 10",
    "3": "x = 7",
    "4": "x = 3"
  },
  "correct_answer": "1",
  "difficulty": 1,
  "order": 1,
  "is_solved": false,
  "attempts_count": 0
}
```

---

#### POST `/tasks/{id}/submit/`
Отправить ответ на задачу. **Требует аутентификации.**

**Request Body:**
```json
{
  "answer": "1"
}
```

**Response (200) - Правильный ответ:**
```json
{
  "success": true,
  "is_correct": true,
  "is_solved": true,
  "attempts": 1,
  "points_earned": 10,
  "correct_answer": null,
  "message": "Правильно! 🎉"
}
```

**Response (200) - Неправильный ответ:**
```json
{
  "success": true,
  "is_correct": false,
  "is_solved": false,
  "attempts": 1,
  "points_earned": 0,
  "correct_answer": null,
  "message": "Неправильно, попробуйте еще раз"
}
```

**Response (200) - После 3 попыток показывается правильный ответ:**
```json
{
  "success": true,
  "is_correct": false,
  "is_solved": false,
  "attempts": 3,
  "points_earned": 0,
  "correct_answer": "1",
  "message": "Неправильно, попробуйте еще раз"
}
```

---

### 📊 Прогресс

#### GET `/progress/`
Получить прогресс пользователя по всем предметам. **Требует аутентификации.**

**Response (200):**
```json
{
  "progress": [
    {
      "subject_id": 1,
      "subject_title": "Математика",
      "subject_icon": "🔢",
      "subject_color": "#3B82F6",
      "total_tasks": 100,
      "completed_tasks": 25,
      "progress_percentage": 25
    }
  ],
  "total_xp": 150,
  "streak": 5
}
```

---

#### GET `/progress/topic/{topic_id}/`
Получить прогресс пользователя по конкретной теме. **Требует аутентификации.**

**Response (200):**
```json
{
  "topic": {
    "id": 1,
    "title": "Алгебра",
    "total_tasks": 20,
    "completed_tasks": 5,
    "progress_percentage": 25
  },
  "tasks": [
    {
      "task_id": 1,
      "question": "Решите уравнение: 2x + 5 = 15",
      "order": 1,
      "is_solved": true,
      "attempts": 1
    }
  ],
  "total_tasks": 20,
  "completed_tasks": 5,
  "progress_percentage": 25
}
```

---

### 🏆 Leaderboard

#### GET `/leaderboard/`
Получить таблицу лидеров (топ 100).

**Response (200):**
```json
{
  "leaderboard": [
    {
      "id": 1,
      "user_profile": {
        "id": 1,
        "user": {
          "id": 1,
          "username": "testuser",
          "first_name": "Иван",
          "last_name": "Иванов"
        },
        "phone": "+992000000000",
        "streak": 10,
        "xp": 500
      },
      "points": 500,
      "updated": "2025-01-02T10:30:00Z"
    }
  ],
  "user_rank": 15
}
```

---

### 📈 Статистика

#### GET `/stats/`
Получить детальную статистику пользователя. **Требует аутентификации.**

**Response (200):**
```json
{
  "profile": {
    "id": 1,
    "user": {...},
    "phone": "+992000000000",
    "streak": 5,
    "xp": 150
  },
  "total_solved": 25,
  "total_attempts": 30,
  "subjects_stats": [
    {
      "subject_id": 1,
      "subject_title": "Математика",
      "subject_icon": "🔢",
      "total_tasks": 100,
      "solved_tasks": 25,
      "progress_percentage": 25
    }
  ],
  "leaderboard_rank": 15
}
```

---

## Коды ошибок

- `200` - Успешный запрос
- `201` - Ресурс создан
- `400` - Неверный запрос (валидация)
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Ресурс не найден
- `500` - Ошибка сервера

## Примеры использования

### Python (requests)

```python
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Вход
response = requests.post(f"{BASE_URL}/auth/login/", json={
    "username": "testuser",
    "password": "password123"
})
data = response.json()
access_token = data['tokens']['access']

# Получить предметы
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/home/", headers=headers)
print(response.json())
```

### Flutter (Dart)

```dart
import 'package:dio/dio.dart';

final dio = Dio(BaseOptions(
  baseUrl: 'http://127.0.0.1:8000/api/v1',
));

// Вход
final loginResponse = await dio.post('/auth/login/', data: {
  'username': 'testuser',
  'password': 'password123',
});
final accessToken = loginResponse.data['tokens']['access'];

// Получить предметы
dio.options.headers['Authorization'] = 'Bearer $accessToken';
final homeResponse = await dio.get('/home/');
print(homeResponse.data);
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://127.0.0.1:8000/api/v1';

// Вход
const loginResponse = await fetch(`${BASE_URL}/auth/login/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'testuser',
    password: 'password123'
  })
});
const { tokens } = await loginResponse.json();

// Получить предметы
const homeResponse = await fetch(`${BASE_URL}/home/`, {
  headers: { 'Authorization': `Bearer ${tokens.access}` }
});
const data = await homeResponse.json();
console.log(data);
```
