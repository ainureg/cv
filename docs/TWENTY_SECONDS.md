# Twenty Seconds: архивная ветка

Вариант с круглой фотографией, боковой панелью и исходным `twentysecondcv.cls` сохранён в **`archive/twenty-seconds`**. Ветка создана от текущего рабочего состояния сайта и данных перед переходом на простой PDF.

Основной сайт и JSON не нужно переключать на старую ветку. Для разовой сборки на свежих данных создайте отдельный worktree. Из корня текущего репозитория:

```bash
git worktree add /tmp/cv-twenty-seconds archive/twenty-seconds
sudo apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-lang-cyrillic lmodern poppler-utils
python /tmp/cv-twenty-seconds/scripts/build_twenty_seconds.py --content "$PWD/content.json" --output /tmp/ainur-karimov-twenty-seconds.pdf
```

Результат: `/tmp/ainur-karimov-twenty-seconds.pdf`. Рядом будет папка `ainur-karimov-twenty-seconds-source` с `.tex`, `.cls` и фотографией для ручной правки. Сайт и его скачиваемый PDF не меняются. Проверяется одна страница A4 и отсутствие переполнения, в том числе в боковой панели.

При повторном использовании существующего worktree первый шаг пропускается. После завершения:

```bash
git worktree remove /tmp/cv-twenty-seconds
```

Архивный макет не синхронизируется с основной веткой автоматически. Свежие факты передаются явно через `--content`; не нужно поддерживать вторую копию резюме. Если схема JSON существенно изменится, может потребоваться поправить архивный адаптер. Текущие варианты с `companyId` и исходными inline-компаниями поддерживаются.

Ветка локальная, пока явно не отправлена в GitHub. Для переноса на другую машину её нужно также запушить, когда будет разрешена публикация.
