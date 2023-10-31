import os
import signal
import subprocess
import streamlit as st
from developer import PythonDeveloper

st.title("Python developer")

user_input = st.text_input("你想实现什么功能:")


def proc_handle(proc):
    button = st.button("停止")
    while True:
        line = proc.stdout.readline()
        if line:
            st.write(line)
        if subprocess.Popen.poll(proc) == 0:  # 判断子进程是否结束
            st.spinner("Running end...")
            print("Running end...")
            break
        else:
            if button:
                st.text("停止中")
                # proc.kill()
                # proc.wait()
                st.text(os.killpg(proc.pid, signal.SIGUSR1))
                proc.wait()
                st.text("停止完毕")
                break
    return proc.returncode




if st.button('Generate'):
    assistant = PythonDeveloper()
    with st.spinner("generate code..."):
        code, explain = assistant.generate_code(user_input)
    st.subheader("Generated code:")
    st.code(code, language='python')
    # enhance= st.text_input("针对生成的代码你想如何优化:")
    # st.button('enhance',on_click=enhance_code,args=(developer,enhance))
    if explain:
        st.write(explain)
    st.subheader("Console Log:")
    with st.spinner("Running code..."):
        proc = assistant.run_script_async()
        proc_handle(proc)
