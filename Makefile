# Makefile for source rpm: rpm
# $Id$
NAME := rpm
SPECFILE = $(firstword $(wildcard *.spec))

include ../common/Makefile.common
