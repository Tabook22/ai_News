# Daily magazine refresh

The magazine refreshes itself every day at **01:00 Asia/Muscat** on the VPS.

- Timer: `ainews-daily.timer`
- Worker: `ainews-daily.service`
- Script: `/var/www/ainews/daily_brief.py`
- User: `www-data`
- Log: `/var/www/ainews/logs/daily_brief.log`
- Journal: `journalctl -u ainews-daily.service`

## What it refreshes

Each run:

1. fetches up to five new AI stories for **Latest News / The world**;
2. refreshes the **Watch / YouTube** shelves;
3. chooses the **front-page spotlight**;
4. refreshes **most-downloaded models** from Hugging Face;
5. files the previous issue and moves older stories to the **archive**.

## What stays editor-controlled

The **Department**, **Project ideas**, **Downloads**, and **Reference library** are
curated sections. They do not have a reliable automatic source, so the daily job
does not invent entries for them. Add verified material through the admin.

## Commands

```bash
# what is scheduled?
systemctl list-timers ainews-daily.timer --no-pager

# run it now (waits for completion)
systemctl start ainews-daily.service

# follow logs
journalctl -u ainews-daily.service -f

# last run summary
tail -20 /var/www/ainews/logs/daily_brief.log

# reinstall the timer after editing the unit files
bash /var/www/ainews/deploy/install_daily_job.sh
```

`Persistent=true` means a missed 01:00 run is executed after the VPS comes back up.
