#ifndef KFILTER_HPP
#define KFILTER_HPP

#include <array>
#include <vector>

namespace loudness {
    class KFilter {
    public:
        KFilter(double samplerate, unsigned int channels);
        double apply(double src, unsigned int channel);

        /**
         * @brief manually flush floats to zero for channel
         * @warning Use architecture FTZ if available for better optimization
         * @param channel
         */
        void manuallyFTZ(unsigned int channel);

    private:
        static constexpr std::size_t FILTER_STATE_SIZE = 5;
        /** BS.1770 filter state. */
        using filter_state = std::array<double, FILTER_STATE_SIZE>;
        /** BS.1770 filter coefficients (nominator). */
        std::array<double, 5> b_;
        /** BS.1770 filter coefficients (denominator). */
        std::array<double, 5> a_;
        /** one filter_state per channel. */
        std::vector<filter_state> v_;
    };
} // namespace loudness
#endif  // KFILTER_HPP
