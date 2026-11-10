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

Ветка опубликована в GitHub. На другой машине сначала выполните `git fetch origin`; при необходимости создайте локальную ветку командой `git branch --track archive/twenty-seconds origin/archive/twenty-seconds`.

В архивном экспорте восстановлены контактные значки Font Awesome. Обучение выводится в боковой панели, математические достижения и кликабельная ссылка на сертификаты — в основной колонке. Данные берутся из текущих `training`, `mathematicsAwards` и `certificatesUrl`.

## Ещё более ранний оригинал

Исходное резюме **до появления сайта**, без изменений исходного `.tex`, класса и фотографии, отдельно сохранено в `archive/twenty-seconds-original`. Основа — последний коммит перед разработкой сайта, `5ec6714`. В этой ветке также есть старый PDF из исходной рабочей папки и инструкция `docs/BUILD.md`.

Для просмотра без переключения основной ветки:

```bash
git fetch origin
git worktree add /tmp/cv-original archive/twenty-seconds-original
```

Готовый исторический PDF: `/tmp/cv-original/cv_karimov_ainur.pdf`. Сборка из сохранённого LaTeX описана в `/tmp/cv-original/docs/BUILD.md`. В отличие от `archive/twenty-seconds`, оригинал не связан с текущим JSON и сохраняется как исторический снимок.
