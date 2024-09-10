from telegram import InlineKeyboardButton

SETTINGS_MARKUP = {
    "main-menu-set": [
        [
            InlineKeyboardButton("⚠️ اخطار پاک سازی پیام", callback_data="warning|"),
            InlineKeyboardButton("📛 تغییر نام نمایشی", callback_data="change-name|"),
        ],
        [
            InlineKeyboardButton("🎵 تگ آهنگ", callback_data="audio-tag|"),
            InlineKeyboardButton("#️⃣ تگ دلخواه", callback_data="custom-tag|"),
        ],
        [
            InlineKeyboardButton("🚫 آنبلاک شدن خودت", callback_data="unblock-me|"),
            InlineKeyboardButton("🚫 آنبلاک همه", callback_data="unblock-all|"),
        ],
    ],
    # TODO clbk for formatting
    "formatting": InlineKeyboardButton(
        "❔قالب بندی چیه", callback_data="what-is-formatting"
    ),
    "back-to-menu": InlineKeyboardButton(
        "↪️ بازگشت به منوی اصلی", callback_data="settings-menu"
    ),
    "nvm-back-to-menu": InlineKeyboardButton(
        "↪️ بیخیالش برگرد منوی اصلی", callback_data="settings-menu"
    ),
    "warning-activate": InlineKeyboardButton(
        "✅ فعالسازی", callback_data="warning|activate"
    ),
    "warning-deactivate": InlineKeyboardButton(
        "❌ غیرفعالسازی", callback_data="warning|deactivate"
    ),
    "remove-custom-tag": InlineKeyboardButton(
        "🗑 پاک کردن تگ دلخواه", callback_data="rm-custom-tag"
    ),
    "remove-audio-tag": InlineKeyboardButton(
        "🗑 پاک کردن تگ آهنگ", callback_data="rm-audio-tag"
    ),
}

MYLINKS_MARKUP = {
    "default-set": [
        [
            InlineKeyboardButton(
                "➕ اضافه کردن لینک جدید",
                callback_data=f"add-link",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔧 شخصی سازی لینک",
                callback_data=f"ch-link",
            ),
            InlineKeyboardButton(
                "❌ حذف کردن لینک",
                callback_data=f"rm-link",
            ),
        ],
        [
            InlineKeyboardButton(
                "❔چرا چندتا لینک داشته باشم",
                callback_data=f"more-links",
            ),
        ],
    ],
    "back-to-menu": InlineKeyboardButton(
        "↪️ برگشت به منوی اصلی",
        callback_data=f"mylinks-menu",
    ),
    "what-is-cid": InlineKeyboardButton(
        f"❔آیدی لینک چیه",
        callback_data=f"what-is-cid|",
    ),
    "what-is-customize": InlineKeyboardButton(
        f"❔شخصی سازی لینک چیه",
        callback_data=f"what-is-cid|",
    ),
}
