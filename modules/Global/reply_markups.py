from telegram import InlineKeyboardButton

SETTINGS_MARKUP = {
    "main-menu-set": [
        [
            InlineKeyboardButton(
                "⌨️ ارسال پیام بدون لینک | ریپلای به کانال",
                callback_data="easier-answer|",
            ),
        ],
        [
            InlineKeyboardButton(
                "✍️ ارسال به ادمین خاص کانال",
                callback_data="channel-signature|",
            ),
        ],
        [
            InlineKeyboardButton("🔗 پیشنمایشِ لینک", callback_data="wpp|"),
            InlineKeyboardButton(
                "👌 ارسال پیامهای پیوسته", callback_data="media-settings|"
            ),
        ],
        [
            InlineKeyboardButton(
                "🖋 ریپلای به بخشی از پیام", callback_data="reply-quote|"
            ),
            InlineKeyboardButton(
                "👀 نمایش دکمه سین زدن", callback_data="seen-settings|"
            ),
        ],
        [
            InlineKeyboardButton("⚠️ اخطار پاک سازی پیام", callback_data="warning|"),
            InlineKeyboardButton("📛 تغییر نام نمایشی", callback_data="change-name|"),
        ],
        [
            InlineKeyboardButton("#️⃣ تگ آهنگ", callback_data="audio-tag|"),
            InlineKeyboardButton("#️⃣ تگ دلخواه", callback_data="custom-tag|"),
        ],
        [
            InlineKeyboardButton("🚫 آنبلاک شدن خودت", callback_data="unblock-me|"),
            InlineKeyboardButton("🚫 آنبلاک همه", callback_data="unblock-all|"),
        ],
    ],
    "formatting": InlineKeyboardButton(
        "❔قالب بندی چیه", callback_data="what-is-formatting"
    ),
    "back-to-menu": InlineKeyboardButton(
        "↪️ بازگشت به منوی اصلی", callback_data="settings-menu"
    ),
    "nvm-back-to-menu": InlineKeyboardButton(
        "↪️ بیخیالش برگرد منوی اصلی", callback_data="settings-menu"
    ),
    "wpp-activate": InlineKeyboardButton(
        "✅ برگشت به حالت پیشفرض", callback_data="wpp|activate"
    ),
    "wpp-deactivate": InlineKeyboardButton(
        "❌ غیرفعال سازی اجباری", callback_data="wpp|deactivate"
    ),
    "warning-activate": InlineKeyboardButton(
        "✅ فعالسازی", callback_data="warning|activate"
    ),
    "warning-deactivate": InlineKeyboardButton(
        "❌ غیرفعالسازی", callback_data="warning|deactivate"
    ),
    "seen-activate": InlineKeyboardButton(
        "✅ فعالسازی", callback_data="seen-settings|activate"
    ),
    "seen-deactivate": InlineKeyboardButton(
        "❌ غیرفعالسازی", callback_data="seen-settings|deactivate"
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

CANCEL_BUTTON = InlineKeyboardButton("بیخیالش", callback_data="cancel")


class MSG_BTN:
    REPLIED_TO = "ریپلای شده به این پیام"
    REPLY = "⌨️ ارسال جواب"
    SEEN = "✅ سین بزن"
    SEEN_DONE = "☑️ سین زدم"
    BLOCK = "🔒 بلاک"
    UNBLOCK = "🔓 آنبلاک"
    REPORT = "⚠️ ریپورت"
