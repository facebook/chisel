PREFIX ?= /usr/local/lib

install:
	xcodebuild \
		-scheme Chisel \
		-configuration Release \
		-sdk iphonesimulator \
		install \
		LD_DYLIB_INSTALL_NAME="$(LD_DYLIB_INSTALL_NAME)" \
		DSTROOT=/ \
		INSTALL_PATH="$(PREFIX)"
