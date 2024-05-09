import asyncio
import logging
import sys
from os import getenv
import re
import aiohttp

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message, ReactionTypeEmoji


TOKEN: str = getenv('TELEGRAM_BOT_TOKEN')
GITLAB_URL: str = getenv('GITLAB_URL')
PROJECT_ID: int = int(getenv('PROJECT_ID'))
PRIVATE_TOKEN: str = getenv('PRIVATE_TOKEN')
TEST_JOB_NAME: str = getenv('TEST_JOB_NAME')
RECHECK_PERIOD: int = int(getenv('RECHECK_PERIOD', '60'))
MR_REGEXP: str = getenv('MR_REGEXP')  # .*https://mygitlab.com/my_project/-/merge_requests/(?P<mr_id>\d+)(/.*)?

dp = Dispatcher()
for_check = []

status_react_dict = {
    # gitlab statuses
    'success': '👍',
    'failed': '👎',
    'running': '🤔',
    'pending': '🤔',
    # service reacts
    'DEFAULT': '👀',
    'HANDLED': '👀',
    'NO_PIPELINE': '🤷',
}

logger = logging.getLogger(__name__)


async def check_pytest(mr_id: int, msg: Message):
    logger.info('Checking pipeline status for MR #%d', mr_id)
    async with aiohttp.ClientSession(headers={'PRIVATE-TOKEN': PRIVATE_TOKEN}) as session:
        async with session.get(f'{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/merge_requests/{mr_id}', ssl=False) as resp:
            json_resp = await resp.json()
            head_pipeline = json_resp.get('head_pipeline')
            if not head_pipeline:
                logger.warning('No head pipeline for MR #%d', mr_id)
                await msg.react([ReactionTypeEmoji(emoji=status_react_dict['NO_PIPELINE'])])
                return
            pid = int(json_resp['head_pipeline']['id'])
            logger.info('Head pipeline id for MR #%d is %d', mr_id, pid)
        async with session.get(f'{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines/{pid}/jobs', ssl=False) as resp:
            jobs = await resp.json()
            logger.info('Found %d jobs for pipeline %d', len(jobs), pid)
            pytest_job = [job for job in jobs if job['name'] == TEST_JOB_NAME][0]
            if not pytest_job:
                logger.error('Job %s not found', TEST_JOB_NAME)
    reaction = status_react_dict.get(pytest_job['status']) or status_react_dict['DEFAULT']
    await msg.react([ReactionTypeEmoji(emoji=reaction)])
    if pytest_job['status'] == 'running':
        for_check.append((mr_id, msg))
        logger.info('Job %s for MR #%d is still running, lets check it later', TEST_JOB_NAME, mr_id)


async def recheck_worker():
    while True:
        await asyncio.sleep(RECHECK_PERIOD)
        logger.info('Check for running jobs')
        if len(for_check) == 0:
            continue
        tmp = for_check.copy()
        for_check.clear()
        for mr_id, msg in tmp:
            await check_pytest(mr_id, msg)


@dp.message()
async def msg_handler(message: types.Message) -> None:
    if not message.text:
        return
    m = re.match(MR_REGEXP, message.text)
    if not m:
        return
    mr_id = int(m.groupdict().get('mr_id'))
    logger.info('Handled message with MR #%d', mr_id)
    await message.react([ReactionTypeEmoji(emoji=status_react_dict['HANDLED'])])
    await check_pytest(mr_id, message)


async def main_bot() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


async def main_async() -> None:
    async with asyncio.TaskGroup() as group:
        group.create_task(main_bot())
        group.create_task(recheck_worker())


def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
