import requests
import json
import time
import xml.etree.ElementTree as ET
from lib.console import Console

class Jenkins():
    def __init__(self, base_url):
        self.con = Console()
        self.base = base_url
        self.view_cache = {}

    def enable(self, view_name, do_not_enable_child):
        if do_not_enable_child:
            self.con.out("Enabling view " + view_name + " and resuming all enabled children...", self.con.White)
        else:
            self.con.out("Enabling view " + view_name + " and all children...", self.con.White)
        if self.trigger_post(self.base + '/job/' + view_name + '/enable'):
            if not do_not_enable_child:
                tasks = self.view(view_name)
                for t in tasks:
                    self.con.out("- Enabling job " + t + "...", self.con.White)
                    self.trigger_post(self.base + '/job/' + t + '/enable')
            return True
        return False

    def wait_until_task_done(self, task_name, build_num):
        self.con.out(".", self.con.White)
        while not self.task_done(task_name, build_num):
            time.sleep(2)
            self.con.out(".", self.con.White)

    def task_done(self, task_name, build_num):
        result = self.get(self.base + '/job/' + task_name + '/api/json')
        if result['nextBuildNumber'] == build_num:
            return False
        if result['inQueue']:
            return False
        if result['color'] in ['blue', 'red']:
            return True
        return False

    def build(self, view_name):
        self.con.outln("Building view " + view_name + "...", self.con.White)
        tasks = self.view(view_name)
        retry_tasks = []
        critical_fail = []
        retry_max = 3
        retry_count = 0
        while len(tasks) > 0 and retry_count <= retry_max:
            for t in tasks:
                result = self.get(self.base + '/job/' + t + '/api/json')
                if result['color'] != 'disabled':
                    nextBuildNumber = result['nextBuildNumber']
                    self.con.out("- Building job " + t + " #" + str(nextBuildNumber) + "...", self.con.White)
                    if self.trigger_post(self.base + '/job/' + t + '/build', False):
                        self.wait_until_task_done(t, nextBuildNumber)
                        stat = self.grep_stat(t, nextBuildNumber)
                        fail_count = stat.attrib['fail']
                        pass_count = stat.attrib['pass']
                        if fail_count == "0":
                            self.con.outln("PASSED [" + pass_count + "/" + pass_count + "]", self.con.Green)
                            self.con.out("--= Disabling job " + t + "...", self.con.White)
                            self.trigger_post(self.base + '/job/' + t + '/disable')
                        else:
                            self.con.outln("FAILED [" + pass_count + "/" + str(int(pass_count) + int(fail_count)) + "]", self.con.Red)
                            should_retry = self.analyze_error_log(t, nextBuildNumber)
                            if should_retry:
                                retry_tasks.append(t)
                            else:
                                critical_fail = critical_fail.append(t)
                else:
                    self.con.outln("- Skipping job " + t + " due to job is disabled...", self.con.White)
            if len(retry_tasks) > 0:
                retry_count += 1
                self.con.outln("Retry #" + str(retry_count) + " : " + str(len(retry_tasks)) + " task(s)", self.con.White)
                tasks = retry_tasks
                retry_tasks = []
            else:
                tasks = []
        if len(tasks) == 0 and len(critical_fail) == 0:
            self.con.outln("ALL TEST PASSED", self.con.Green)
            self.con.out("- Running clean up task for " + view_name + "...", self.con.White)
            result = self.get(self.base + '/job/' + view_name + '/api/json')
            nextBuildNumber = result['nextBuildNumber']
            if self.trigger_post(self.base + '/job/' + view_name + '/build', False):
                self.wait_until_task_done(view_name, nextBuildNumber)
            self.con.outln("OK", self.con.Green)
            self.con.out("- Disabling view " + view_name + "...", self.con.White)
            self.trigger_post(self.base + '/job/' + view_name + '/disable')

    def analyze_error_log(self, task_name, build_num):
        return True

    def grep_stat(self, task_name, build_num):
        result = self.get(self.base + '/job/' + task_name + '/' + str(build_num) + '/robot/report/output.xml')
        stat = result.findall('./statistics/total/stat')
        return stat[-1]

    def view(self, view_name):
        if view_name not in self.view_cache or self.view_cache[view_name] == None:
            result = self.get(self.base + '/job/' + view_name + '/api/json')
            if result != None:
                out = []
                for p in result['downstreamProjects']:
                    out.append(p['name'])
                self.view_cache[view_name] = out
                return out
            else:
                self.view_cache[view_name] = None
        return self.view_cache[view_name]

    def trigger_get(self, url, verbose = False):
        resp = requests.get(url)
        if resp.status_code == 200 or resp.status_code == 201:
            if verbose:
                self.con.outln("OK", self.con.Green)
            return True
        else:
            if verbose:
                self.con.outln("FAILED", self.con.Red)
            return False

    def trigger_post(self, url, verbose = True):
        resp = requests.post(url)
        if resp.status_code == 200 or resp.status_code == 201:
            if verbose:
                self.con.outln("OK", self.con.Green)
            return True
        else:
            if verbose:
                self.con.outln("FAILED", self.con.Red)
            return False

    def get(self, url):
        resp = requests.get(url)
        content_type = resp.headers['content-type'].split(';')[0]
        if resp.status_code == 200 or resp.status_code == 201:
            if content_type in ['application/json', 'text/json']:
                js = json.loads(resp.content)
                return js
            elif content_type in ['application/xml']:
                root = ET.fromstring(resp.content)
                return root
        return None
