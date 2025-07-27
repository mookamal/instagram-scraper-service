# 📸 Instagram Scraper Service

A high-performance API service built with **FastAPI** to scrape public data from Instagram using rotating proxies, browser automation, and direct GraphQL/private endpoints.

> ⚠️ **Use responsibly.** This tool is intended for educational or research purposes only. Scraping data from Instagram may violate their Terms of Service.

---

## 🚀 Features

- 🔍 Scrape public **user profiles** (followers, bio, profile picture, etc.)
- ❤️ Fetch exact **like counts** from posts via GraphQL
- 🌐 Smart proxy management using **undetected_chromedriver**
- 🛡️ Cookie & user-agent caching per proxy for 24h to avoid detection
- 🧱 Modular & versioned API structure (`/api/v1/...`)
- 🔐 Optional API key authentication (via config)
- 🧪 Debug endpoints to inspect system settings (development only)

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **FastAPI** – modern Python web framework
- **Uvicorn** – blazing-fast ASGI server
- **Undetected-Chromedriver** – headless Chrome with anti-bot evasion
- **Requests** – lightweight HTTP requests for GraphQL/API
- **Pydantic** – clean configuration via environment variables

---

## ⚙️ How It Works

- Each proxy is tied to a headless Chrome session (`ProxySession`) that:
  - Launches undetected Chrome
  - Loads a dummy Instagram page
  - Extracts cookies & user-agent
  - Reuses session for 24h (to reduce overhead)

- Instagram scraping relies on:
  - `https://www.instagram.com/api/v1/users/web_profile_info/` — for user data  
  - `https://www.instagram.com/graphql/query/` — for post like counts

- API endpoints wrap these actions and expose clean JSON responses.

---

## 📦 Installation

```bash
git clone https://github.com/mookamal/instagram-scraper-service.git
cd instagram-scraper-service
pip install -r requirements.txt
