PREFIX ?= /usr/local/lib

export INSTALL_NAME =
ifneq ($(LD_DYLIB_INSTALL_NAME),)
	INSTALL_NAME = "LD_DYLIB_INSTALL_NAME=$(LD_DYLIB_INSTALL_NAME)"
endif

install:
	xcodebuild \
		-scheme Chisel \
		-configuration Release \
		-sdk iphonesimulator \
		install \
		$(INSTALL_NAME) \
		DSTROOT=/ \
		INSTALL_PATH="$(PREFIX)"
