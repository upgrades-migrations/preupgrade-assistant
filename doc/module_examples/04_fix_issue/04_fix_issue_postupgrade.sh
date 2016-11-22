#!/bin/sh

yum install -y naughty-foo-house || {
  echo >&2 "Error: The 'naughty-foo-house' package has not been installed."
  echo >&2 "       Install it manually."
  exit 1
}

