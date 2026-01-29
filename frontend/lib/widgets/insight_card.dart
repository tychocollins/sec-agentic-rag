import 'dart:ui';
import 'package:flutter/material.dart';

/// A futuristic neon-styled card for displaying SEC analysis insights.
class InsightCard extends StatefulWidget {
  final String answer;
  final List<String> citations;
  final String ticker;
  final int year;

  const InsightCard({
    super.key,
    required this.answer,
    required this.citations,
    required this.ticker,
    required this.year,
  });

  @override
  State<InsightCard> createState() => _InsightCardState();
}

class _InsightCardState extends State<InsightCard>
    with SingleTickerProviderStateMixin {
  bool _showCitations = false;
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;

  // Neon color palette
  static const Color neonCyan = Color(0xFF00F5FF);
  static const Color neonBlue = Color(0xFF00BFFF);
  static const Color neonPurple = Color(0xFF9D00FF);
  static const Color darkBg = Color(0xFF0A0E17);
  static const Color cardBg = Color(0xFF0D1321);

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );
    _fadeAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    );
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              decoration: BoxDecoration(
                color: cardBg.withAlpha(230),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: neonCyan.withAlpha(80),
                  width: 1,
                ),
                boxShadow: [
                  BoxShadow(
                    color: neonCyan.withAlpha(30),
                    blurRadius: 20,
                    spreadRadius: 0,
                  ),
                  BoxShadow(
                    color: neonBlue.withAlpha(20),
                    blurRadius: 40,
                    spreadRadius: 5,
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeader(),
                  _buildAnswerSection(),
                  if (widget.citations.isNotEmpty) _buildCitationsSection(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            neonCyan.withAlpha(25),
            neonBlue.withAlpha(15),
            Colors.transparent,
          ],
        ),
        border: Border(
          bottom: BorderSide(color: neonCyan.withAlpha(40)),
        ),
      ),
      child: Row(
        children: [
          // Ticker badge with neon glow
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: neonCyan.withAlpha(20),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: neonCyan.withAlpha(150)),
              boxShadow: [
                BoxShadow(
                  color: neonCyan.withAlpha(50),
                  blurRadius: 12,
                  spreadRadius: 0,
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.trending_up, color: neonCyan, size: 16),
                const SizedBox(width: 8),
                Text(
                  widget.ticker,
                  style: TextStyle(
                    color: neonCyan,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                    letterSpacing: 2,
                    shadows: [
                      Shadow(color: neonCyan.withAlpha(150), blurRadius: 10),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          // Year badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white.withAlpha(10),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.white.withAlpha(30)),
            ),
            child: Text(
              'FY ${widget.year}',
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 13,
                fontWeight: FontWeight.w600,
                letterSpacing: 1,
              ),
            ),
          ),
          const Spacer(),
          // SEC verified badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [neonCyan.withAlpha(40), neonBlue.withAlpha(40)],
              ),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: neonCyan.withAlpha(100)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.verified, color: neonCyan, size: 14),
                const SizedBox(width: 6),
                Text(
                  'SEC 10-K',
                  style: TextStyle(
                    color: neonCyan,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAnswerSection() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Text(
        widget.answer,
        style: const TextStyle(
          fontSize: 16,
          height: 1.7,
          color: Colors.white,
          fontWeight: FontWeight.w400,
          letterSpacing: 0.3,
        ),
      ),
    );
  }

  Widget _buildCitationsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Neon divider
        Container(
          margin: const EdgeInsets.symmetric(horizontal: 20),
          height: 1,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                Colors.transparent,
                neonCyan.withAlpha(100),
                neonBlue.withAlpha(100),
                Colors.transparent,
              ],
            ),
          ),
        ),
        // Citations toggle
        InkWell(
          onTap: () => setState(() => _showCitations = !_showCitations),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            child: Row(
              children: [
                Icon(Icons.source_outlined, size: 18, color: neonCyan),
                const SizedBox(width: 10),
                Text(
                  '${widget.citations.length} Source${widget.citations.length > 1 ? 's' : ''} from SEC Filing',
                  style: TextStyle(
                    fontSize: 13,
                    color: neonCyan.withAlpha(200),
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.5,
                  ),
                ),
                const Spacer(),
                AnimatedRotation(
                  turns: _showCitations ? 0.5 : 0,
                  duration: const Duration(milliseconds: 200),
                  child: Icon(Icons.expand_more, color: neonCyan),
                ),
              ],
            ),
          ),
        ),
        // Citations list
        AnimatedCrossFade(
          firstChild: const SizedBox.shrink(),
          secondChild: _buildCitationsList(),
          crossFadeState: _showCitations
              ? CrossFadeState.showSecond
              : CrossFadeState.showFirst,
          duration: const Duration(milliseconds: 250),
        ),
      ],
    );
  }

  Widget _buildCitationsList() {
    return Container(
      margin: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.black.withAlpha(100),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: neonCyan.withAlpha(30)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: widget.citations.take(5).map((citation) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  margin: const EdgeInsets.only(top: 6),
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    color: neonCyan,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(color: neonCyan, blurRadius: 6),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    citation.length > 200
                        ? '${citation.substring(0, 200)}...'
                        : citation,
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.white.withAlpha(200),
                      height: 1.6,
                    ),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}
