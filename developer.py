import json
import re, subprocess
import time
import requests
from venv import create
from dotenv import load_dotenv
from prompts import SYSTEM_MESSAGE




class PythonDeveloper:
    def __init__(self, script_path="temp.py"):
        load_dotenv()
        self.venv_dir = "./venv"
        self.user_msg = list()
        # developer.create_venv()
        self.script_path = script_path

    def get_messages(self):
        return [{'role': 'system', 'content': SYSTEM_MESSAGE}, {'role': 'user', 'content': '\n'.join(self.user_msg)}]

    def send_request(self):
        data = {
            "temperature": 0.7,
            "messages": self.get_messages()
        }
        url = 'http://172.20.160.64:9000/openai/deployments/gpt-4/chat/completions?api-version=2023-08-01-preview'
        headers = {'Content-Type': 'application/json'}
        retry = 3
        while retry - 1:
            try:
                response = requests.post(url, headers=headers, json=data)
                print(response.text)
                response_data = response.json()
                return response_data
            except json.decoder.JSONDecodeError:
                continue

    def create_venv(self):
        # create(developer.venv_dir, with_pip=True)
        pass

    def add_msg(self, message):
        self.user_msg.append(message)

    def extract_code(self, response: str):
        return {t: re.findall(rf"```{t}\s*([\s\S]*?)```", response) for t in ["python", "bash", "explain"]}

    def install_deps(self, dependencies, type):
        if type == "bash":
            for dep in dependencies:
                if not dep.startswith('#') and dep.startswith("pip"):
                    try:
                        subprocess.check_call(dep.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                              universal_newlines=True, timeout=120)
                    except  Exception as e:
                        print(f"install err:{e}")

    def run_script(self, timeout=None):
        return subprocess.run(f"{self.venv_dir}/bin/python {self.script_path}", capture_output=True, text=True,
                              check=True,
                              timeout=timeout, shell=True, close_fds=True)

    def run_script_async(self):
        return subprocess.Popen([f'{self.venv_dir}/bin/python', self.script_path], stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True, bufsize=1)

    def generate_code(self, prompt: str, attempts=10):
        self.add_msg(prompt)
        for _ in range(attempts):
            print(self.get_messages())

            code = self.extract_code(self.send_request()['choices'][0]['message']['content'])
            try:
                if code.get('bash'):
                    print(f'bash code:\n{code["bash"][0]}')
                    dependencies = []
                    [dependencies.extend(dependency.strip().split('\n')) for dependency in code['bash'] if
                     dependency.strip()]
                    self.install_deps(dependencies, "bash")
                if code.get("python"):
                    print(f'python code:\n{code["python"][0]}')
                    self.add_msg(f"this is the code generated: {code['python'][0]}")
                    with open(self.script_path, "w") as f:
                        f.write('\n'.join(code["python"]))

                else:
                    self.add_msg("Please give the full python code\n")
                    continue
                explain = None
                if code.get("explain"):
                    explain = code['explain'][0]
                proc = self.run_script(timeout=10)

                print(f"退出码:{proc.stdout},{proc.returncode}")
                if proc.returncode != 0:
                    print(f"成功失败：{proc.stderr}")
                else:
                    return code["python"][0], explain
            except subprocess.TimeoutExpired:
                # 说明程序一直在运行
                print(f"超时")
                time.sleep(3)
                return code["python"][0], explain
            except subprocess.CalledProcessError as e:
                print(e.stdout)
                print(e.stderr)
                self.add_msg(
                    f"I got an error when running the code. Can you help me fix it?\n, The error message is as follows:\n{e.stderr}")
            except Exception as e:
                print(f"all Exception:{e}")

        raise ValueError("Max attempts reached. Unable to generate valid code.")


if __name__ == "__main__":
    assistant = PythonDeveloper()
    input_str = input("Enter a prompt: ")
    code = assistant.generate_code(input_str)
    print(f"{code}")
    assistant.run_script()
