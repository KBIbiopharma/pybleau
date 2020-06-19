
class plotDescriptorDeSerializer_v0(plotDescriptorDeSerializer):

    protocol_version = 0

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        # For a short amount of time, new plot_descriptors may have been stored
        # with protocol version at 0 instead of 1, so check:
        if "plot_config" not in kwargs and 'factory_kwargs' in kwargs:
            factory_kw = constructor_data['kwargs'].pop('factory_kwargs')
            # Convert factory kw to configurator kw:
            for key in ["x_arr", "y_arr", "z_arr"]:
                factory_kw.pop(key, None)

            config_klass = DEFAULT_CONFIGS[kwargs['plot_type']]
            style_klass = DEFAULT_STYLES[kwargs['plot_type']]
            style_kw = factory_kw.pop('plot_style')
            factory_kw['plot_style'] = style_klass(**style_kw)
            kwargs["plot_config"] = config_klass(**factory_kw)

        instance = super(plotDescriptorDeSerializer_v0, self).get_instance(
            constructor_data
        )
        return instance


class plotDescriptorDeSerializer_v1(plotDescriptorDeSerializer):

    protocol_version = 1

    def get_instance(self, constructor_data):
        constructor_data['kwargs'].pop("ndim")
        instance = super(plotDescriptorDeSerializer_v1, self).get_instance(
            constructor_data
        )
        return instance
