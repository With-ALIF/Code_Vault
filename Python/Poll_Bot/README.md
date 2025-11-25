#  ALIF Telegram Poll Bot


[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-green?logo=telegram)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](#)

---

## 🚀 Overview

**ALIF Poll Bot** একটি production-ready Telegram automation system যা specially-formatted MCQ text কে Telegram **Quiz Polls**-এ অটোম্যাটিক রূপান্তর করে। এটি high-volume educational channels, coaching centers, MCQ publishers এবং automated exam systems-এর জন্য ডিজাইন করা হয়েছে।

---

## ✨ Highlights

* ✅ **Automatic MCQ → Telegram Quiz Poll conversion**
* ✅ **Per-user channel targeting** (users can set which channel to post polls to)
* ✅ **Customizable prefix/suffix & formatting rules**
* ✅ **Safe multi-user queue system** with concurrency control
* ✅ **Batch sending** with robust rate-limit handling
* ✅ **Persistent storage** for user config and state
* ✅ **Fully async** using `asyncio` and `python-telegram-bot v20+`

---

## 🔧 Features (Detailed)

### 1. MCQ → Telegram Quiz Poll Conversion

* Accepts plain-text MCQ files (supported formats documented below).
* Parses question, options, and correct answer markers and generates **Telegram quiz polls** with correct option set.

### 2. Per-User Channel Targeting

* Each user may define one or more target channels.
* Supports posting to channels or groups where the bot has admin/posting permissions.

### 3. Formatting & Custom Prefix/Suffix

* Add custom prefixes, suffixes, numbering, headers, or footers per-upload or per-user.

### 4. Safe Multi-User Queue System

* Queue architecture prevents collisions and race conditions.
* Worker pool size and concurrency limits are configurable.

### 5. Batch Sending & Rate-Limit Handling

* Sends polls in batches with delay windows and exponential backoff for 429 errors.
* Tested on workloads from **1 → 2000+ polls**.

### 6. Persistent Storage

* Stores user preferences, formatting rules and last-run state in persistent storage (SQLite by default; pluggable to PostgreSQL or Redis).
---

## 🛠️ Technology Stack

* **Python 3.10+**
* **python-telegram-bot v20+** (async)
* **asyncio** concurrency model
* **SQLite** (default) — optional PostgreSQL/Redis
* Optional: Docker for containerized deployment

---

## 📬 Contact

Maintainer: **Alif**

Contribute: **Sadman Prodhan**

---

*Made with ❤️ and lots of async tasks.*
