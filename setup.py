from setuptools import setup

setup(
    name="aftersales",
    version="0.0.1",
    description="售后管理平台演示应用",
    packages=["aftersales", "aftersales.after_sales"],
    install_requires=["frappe"],
)