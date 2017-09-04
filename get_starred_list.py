"""
@date       170904 - Imp

Query starred list from user github and export to markdown file.

IMPORTANT:
  * API limit: 60 times in one hour
  * You could check from 'https://api.github.com/rate_limit' by yourself.

Ref:
  * https://developer.github.com/v3/activity/starring/
  * https://developer.github.com/v3/#pagination
  * https://developer.github.com/v3/rate_limit/
"""
from datetime import datetime, date
import asyncio
import aiohttp


OWNER = 'grtfou'  # ex. gvanrossum
OUTPUT_FILENAME = 'README.md'
API_URL = 'https://api.github.com'


def _repos_checker(lng, proj, last_code_push):
    """
    Design a checker by user defined.
    """

    # For user to check old repository
    if int(last_code_push) > 540:  # 1.5 year
        print("({}, {} days) {}".format(
            lng, last_code_push, proj['full_name']))


async def fetch(client, page=1):
    """Get starred list.
    Other URL arguments:
      * page: ex. 3
      * per_page: ex. 100
    """
    url = '{}/users/{}/starred?page={}&per_page=100'.format(
        API_URL, OWNER, page)
    header = {
        'content-type': 'application/vnd.github.v3+json'
    }
    async with client.get(url, headers=header) as resp:
        assert resp.status == 200
        # print(resp.headers.get('link').split(',')[-1])
        return await resp.json()


async def main(loop):
    data = {}
    async with aiohttp.ClientSession(loop=loop) as client:
        page = 1
        count = 0
        while True:
            try:
                json_repo = await fetch(client, page)
            except AssertionError:
                print('Fetch page fail.')
                break

            if not json_repo:
                break
            else:
                page += 1

            for proj in json_repo:
                count += 1
                lng = proj.get('language', '')
                if lng is None:
                    lng = 'NONE - DOC'
                else:
                    lng = lng.upper()

                if lng in data:
                    data[lng] += [proj]
                else:
                    data[lng] = [proj]

    print("Total starred repos: {}".format(count))
    with open(OUTPUT_FILENAME, 'w') as ffi:
        ffi.write("##### Created at {} by get_starred_list.py\n\n".format(
            date.today()))
        for lng, projs in sorted(data.items(), key=lambda data: data[0]):
            ffi.write("# {} \n\n".format(lng))
            ffi.write("---\n\n")
            for proj in projs:
                pushed_at = datetime.strptime(
                    proj['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")

                last_code_push = str((datetime.utcnow() - pushed_at).days)

                ffi.write("## {} \n\n".format(proj.get('name')))
                ffi.write("'''\n{} \n'''\n\n".format(
                    proj.get('description')))
                ffi.write("  * [Github]({})\n".format(proj['html_url']))
                ffi.write("  * Stars: {}\n".format(proj['stargazers_count']))
                ffi.write("  * Open issues: {}\n".format(
                    proj['open_issues_count']))
                ffi.write("  * Last pushed: {} ({} days)\n\n".format(
                    pushed_at.strftime("%Y-%m-%d"), last_code_push))

                # checker
                _repos_checker(lng, proj, last_code_push)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
