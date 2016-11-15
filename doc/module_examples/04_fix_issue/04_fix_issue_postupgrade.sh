#!/bin/sh

yum install -y naughty-foo-house || {
  echo >&2 "Error: The package naughty-foo-house has not been installed."
  echo >&2 "       You should install it manually."
  exit 1
}

