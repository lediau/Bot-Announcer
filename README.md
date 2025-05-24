# Bot-Announcer


:mega: **Automation Goal**  
Set up a bot to **automatically post:**
- **Schedule messages** every **Monday at 18:00 UTC**  
- **Resource Drops** every **Friday at 18:00 UTC**  
…for **every cohort**.

---

:computer: **Codebase & Files**  
- [GitHub repo](https://github.com/lediau/Bot-Announcer)
- `.env` will be shared here (don’t push it)

---

:white_check_mark: **Weekly Requirements**

**Friday (Resource Drop)**  
→ Each **expert** must [fill out the table](https://docs.google.com/spreadsheets/d/13ShIo5jedb98d2rVHd05NgFkhaIgLpph7-dgBctta1Q/edit?gid=0) **before Friday 18:00 UTC**. It is recommended to fill in advance several weeks as well.

**Monday (Schedule Message)**  
→ Ensure the Notion page structure follows:  
- `h1` Sprint titles: `Sprint S (MONTH N – MONTH N)`  
- `h3` Week titles: `Week X` or `Weeks X–Y`

---

:pushpin: **Where does the bot get channel/doc info?**  
From [this sheet](https://docs.google.com/spreadsheets/d/10SbX-9ZEctP7Zd5WWkmxwztx5R128hwFbHUtfDqgPgQ/edit?gid=0)
Make sure **all cohorts** are added as a row!

---

:bulb: **Future Improvements**
- :white_check_mark: Test across different cohorts
- :repeat: Convert Notion pages to Excel to reduce scraping bugs
- :white_check_mark: Add a confirmation step:  
  → Bot posts a preview in a private channel  
  → Waits for approval  
  → Then posts in public

---

:tools: **TODO**
- [ ] Fill in the [tech details](https://docs.google.com/spreadsheets/d/10SbX-9ZEctP7Zd5WWkmxwztx5R128hwFbHUtfDqgPgQ/edit?gid=0)
- [ ] Tell experts to update [resource table](https://docs.google.com/spreadsheets/d/13ShIo5jedb98d2rVHd05NgFkhaIgLpph7-dgBctta1Q/edit?gid=0)
- [ ] Migrate bot from local:
  - [ ] Host the bot (VPS/cloud/etc.)
  - [ ] Create API keys (Notion, Discord)
  - [ ] Add bot to Notion pages + Discord servers/channels
  - [ ] Etc., I might have forgotten a lot.
