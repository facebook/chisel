PREFIX ?= /usr/local/lib

install:
	xcodebuild \
		-scheme Chisel \
		-configuration Release \
		-sdk iphonesimulator \
		install \
		DSTROOT=/ \
		INSTALL_PATH="$(PREFIX)"
