import 'dart:async';
import 'package:flutter/material.dart';
import 'api_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  final ApiService _apiService = ApiService();
  final List<Map<String, dynamic>> _messages = [];
  final ScrollController _scrollController = ScrollController();
  bool _isLoading = false;
  
  // Time-based progress tracking (non-looping)
  Timer? _progressTimer;
  int _elapsedSeconds = 0;
  int _statusStep = 0;
  bool _isDeepAnalysis = false;
  
  // Progress bar animation (non-linear)
  AnimationController? _progressController;
  double _progressValue = 0.0;
  
  // Step timing thresholds (seconds when each step starts)
  final List<int> _stepTimings = [0, 3, 8, 15, 25, 30, 45];
  
  final List<String> _statusSteps = [
    'Planning analysis strategy...',
    'Searching SEC filings...',
    'Reading 10-K documents...',
    'Extracting financial data...',
    'Cross-referencing information...',
    'Reviewing and synthesizing...',
    'Preparing response...',
  ];
  
  // Quick Facts data
  String? _currentTicker;
  int? _currentYear;

  // High-contrast Light Theme colors
  static const Color offWhite = Color(0xFFF8F9FA);
  static const Color deepSlate = Color(0xFF212529);
  static const Color slateGray = Color(0xFF495057);
  static const Color mediumGray = Color(0xFF6C757D);
  static const Color accentBlue = Color(0xFF2563EB);
  static const Color lightGray = Color(0xFFDEE2E6);
  static const Color cardWhite = Color(0xFFFFFFFF);

  void _startProgressAnimation() {
    _elapsedSeconds = 0;
    _statusStep = 0;
    _isDeepAnalysis = false;
    _progressValue = 0.0;
    
    // Start elapsed time tracker
    _progressTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() {
        _elapsedSeconds++;
        
        // Update step based on elapsed time (non-looping)
        for (int i = _stepTimings.length - 1; i >= 0; i--) {
          if (_elapsedSeconds >= _stepTimings[i]) {
            _statusStep = i;
            break;
          }
        }
        
        // Sticky Step 6 with deep analysis message after 30s
        if (_elapsedSeconds >= 30 && _statusStep == 5) {
          _isDeepAnalysis = true;
        }
        
        // Non-linear progress: 0-30% in 5s, 30-90% over 180s
        if (_elapsedSeconds <= 5) {
          _progressValue = (_elapsedSeconds / 5) * 0.30; // 0-30% in 5s
        } else if (_elapsedSeconds <= 185) {
          _progressValue = 0.30 + ((_elapsedSeconds - 5) / 180) * 0.60; // 30-90% over 3min
        } else {
          _progressValue = 0.90; // Cap at 90% until response
        }
      });
    });
  }

  void _stopProgressAnimation({bool completed = false}) {
    _progressTimer?.cancel();
    _progressTimer = null;
    
    if (completed) {
      setState(() {
        _progressValue = 1.0; // Jump to 100% on success
      });
      // Brief delay to show completion before hiding
      Future.delayed(const Duration(milliseconds: 300), () {
        if (mounted) {
          setState(() {
            _elapsedSeconds = 0;
            _statusStep = 0;
            _isDeepAnalysis = false;
          });
        }
      });
    } else {
      _elapsedSeconds = 0;
      _statusStep = 0;
      _isDeepAnalysis = false;
      _progressValue = 0.0;
    }
  }

  // Comparison tickers
  List<String> _comparisonTickers = [];
  final Map<String, Map<String, dynamic>> _companyQuickFacts = {
    'AAPL': {
      'name': 'Apple Inc.',
      'sector': 'Technology',
      'industry': 'Consumer Electronics',
      'ceo': 'Tim Cook',
      'headquarters': 'Cupertino, CA',
      'employees': '164,000+',
      'netIncome2023': 96995000000, // ~$97B
    },
    'MSFT': {
      'name': 'Microsoft Corporation',
      'sector': 'Technology',
      'industry': 'Software - Infrastructure',
      'ceo': 'Satya Nadella',
      'headquarters': 'Redmond, WA',
      'employees': '221,000+',
      'netIncome2023': 72361000000, // ~$72B
    },
    'GOOGL': {
      'name': 'Alphabet Inc.',
      'sector': 'Technology',
      'industry': 'Internet Content & Information',
      'ceo': 'Sundar Pichai',
      'headquarters': 'Mountain View, CA',
      'employees': '182,000+',
      'netIncome2023': 73795000000, // ~$74B
    },
    'AMZN': {
      'name': 'Amazon.com, Inc.',
      'sector': 'Consumer Cyclical',
      'industry': 'Internet Retail',
      'ceo': 'Andy Jassy',
      'headquarters': 'Seattle, WA',
      'employees': '1,500,000+',
      'netIncome2023': 30425000000, // ~$30B
    },
    'TSLA': {
      'name': 'Tesla, Inc.',
      'sector': 'Consumer Cyclical',
      'industry': 'Auto Manufacturers',
      'ceo': 'Elon Musk',
      'headquarters': 'Austin, TX',
      'employees': '140,000+',
      'netIncome2023': 14997000000, // ~$15B
    },
    'META': {
      'name': 'Meta Platforms, Inc.',
      'sector': 'Technology',
      'industry': 'Internet Content & Information',
      'ceo': 'Mark Zuckerberg',
      'headquarters': 'Menlo Park, CA',
      'employees': '67,000+',
      'netIncome2023': 39098000000, // ~$39B
    },
    'NVDA': {
      'name': 'NVIDIA Corporation',
      'sector': 'Technology',
      'industry': 'Semiconductors',
      'ceo': 'Jensen Huang',
      'headquarters': 'Santa Clara, CA',
      'employees': '29,000+',
      'netIncome2023': 29760000000, // ~$30B
    },
  };

  // Detect tickers from query
  List<String> _detectTickers(String query) {
    final upperQuery = query.toUpperCase();
    final detected = <String>[];
    for (final ticker in _companyQuickFacts.keys) {
      if (upperQuery.contains(ticker)) {
        detected.add(ticker);
      }
    }
    // Also check for common company names
    final nameToTicker = {
      'APPLE': 'AAPL',
      'MICROSOFT': 'MSFT',
      'GOOGLE': 'GOOGL',
      'ALPHABET': 'GOOGL',
      'AMAZON': 'AMZN',
      'TESLA': 'TSLA',
      'META': 'META',
      'FACEBOOK': 'META',
      'NVIDIA': 'NVDA',
    };
    for (final entry in nameToTicker.entries) {
      if (upperQuery.contains(entry.key) && !detected.contains(entry.value)) {
        detected.add(entry.value);
      }
    }
    return detected.take(2).toList(); // Max 2 for comparison
  }

  void _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    // Detect tickers from user query
    final detectedTickers = _detectTickers(text);

    setState(() {
      _messages.add({'role': 'user', 'text': text});
      _isLoading = true;
      // Update comparison tickers immediately from query
      if (detectedTickers.isNotEmpty) {
        _comparisonTickers = detectedTickers;
      }
    });
    _controller.clear();
    _scrollToBottom();
    _startProgressAnimation();

    try {
      int? agentMsgIndex;
      
      await for (final event in _apiService.analyzeStream(text)) {
        if (event['type'] == 'metadata') {
          setState(() {
            agentMsgIndex = _messages.length;
            _messages.add({
              'role': 'agent',
              'answer': '',
              'ticker': event['ticker_used'] ?? "?",
              'year': event['year_used'] ?? 2023,
              'citations': List<String>.from(event['context_used'] ?? []),
              'showCitations': false,
            });
            
            // Update Quick Facts
            _currentTicker = event['ticker_used'];
            _currentYear = event['year_used'];
            if (_currentTicker != null && 
                _companyQuickFacts.containsKey(_currentTicker) &&
                !_comparisonTickers.contains(_currentTicker)) {
              if (_comparisonTickers.isEmpty) {
                _comparisonTickers = [_currentTicker!];
              }
            }
          });
        } else if (event['type'] == 'token' && agentMsgIndex != null) {
          setState(() {
            _messages[agentMsgIndex!]['answer'] += event['text'];
          });
          _scrollToBottom();
        } else if (event['type'] == 'error') {
          throw Exception(event['message']);
        } else if (event['type'] == 'done') {
          _stopProgressAnimation(completed: true);
        }
      }
    } catch (e) {
      setState(() {
        _messages.add({
          'role': 'agent',
          'answer': "Error: $e",
          'ticker': "ERR",
          'year': 0,
          'citations': <String>[],
          'showCitations': false,
        });
      });
      _stopProgressAnimation(completed: false);
    } finally {
      setState(() {
        _isLoading = false;
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  bool get _showHero => _messages.isEmpty;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: offWhite,
      body: Column(
        children: [
          _buildAppBar(),
          Expanded(
            child: Row(
              children: [
                // Left: Conversation + Input (80%)
                Expanded(
                  flex: 4,
                  child: Column(
                    children: [
                      Expanded(
                        child: _showHero ? _buildHeroSection() : _buildConversationPanel(),
                      ),
                      _buildInputSection(),
                    ],
                  ),
                ),
                // Right: Quick Facts Panel (20%) with subtle left border
                Expanded(
                  flex: 1,
                  child: Container(
                    decoration: BoxDecoration(
                      color: cardWhite,
                      border: Border(
                        left: BorderSide(color: lightGray.withAlpha(180), width: 1),
                      ),
                    ),
                    child: _buildQuickFactsPanel(),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAppBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 20),
      decoration: BoxDecoration(
        color: cardWhite,
        border: Border(bottom: BorderSide(color: lightGray)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: accentBlue,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.analytics, color: Colors.white, size: 24),
          ),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'SEC Agent RAG',
                style: TextStyle(
                  color: deepSlate,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'AI-Powered Financial Intelligence',
                style: TextStyle(
                  color: slateGray,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xFF10B981).withAlpha(20),
              borderRadius: BorderRadius.circular(25),
              border: Border.all(color: const Color(0xFF10B981)),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.circle, color: Color(0xFF10B981), size: 10),
                SizedBox(width: 8),
                Text(
                  'System Online',
                  style: TextStyle(
                    color: Color(0xFF10B981),
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeroSection() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(48),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(
                color: accentBlue.withAlpha(15),
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.insights, size: 72, color: accentBlue),
            ),
            const SizedBox(height: 40),
            Text(
              'Your AI Financial Analyst is ready.',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: deepSlate,
                height: 1.3,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'What would you like to verify today?',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: deepSlate,
                height: 1.3,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            Text(
              'Ask about revenue, net income, or compare companies.',
              style: TextStyle(
                fontSize: 18,
                color: slateGray,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildConversationPanel() {
    return Container(
      color: offWhite,
      child: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 24),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                if (msg['role'] == 'user') {
                  return _buildUserMessage(msg['text']);
                } else {
                  return _buildAgentMessage(msg, index);
                }
              },
            ),
          ),
          if (_isLoading) _buildLoadingIndicator(),
        ],
      ),
    );
  }

  Widget _buildUserMessage(String text) {
    return Align(
      alignment: Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 10),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 18),
        decoration: BoxDecoration(
          color: accentBlue,
          borderRadius: BorderRadius.circular(16),
        ),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.45,
        ),
        child: Text(
          text,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w500,
            height: 1.5,
          ),
        ),
      ),
    );
  }

  Widget _buildAgentMessage(Map<String, dynamic> msg, int index) {
    final citations = List<String>.from(msg['citations'] ?? []);
    final showCitations = msg['showCitations'] ?? false;

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: cardWhite,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: lightGray, width: 1.5),
        ),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.5,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: accentBlue.withAlpha(15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: accentBlue.withAlpha(50)),
                    ),
                    child: Text(
                      '${msg['ticker']} · FY${msg['year']}',
                      style: TextStyle(
                        color: accentBlue,
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Icon(Icons.verified, color: accentBlue, size: 20),
                  const SizedBox(width: 6),
                  Text(
                    'SEC 10-K',
                    style: TextStyle(
                      color: accentBlue,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            // Answer
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
              child: Text(
                msg['answer'],
                style: TextStyle(
                  fontSize: 18,
                  color: deepSlate,
                  height: 1.6,
                ),
              ),
            ),
            // Citations dropdown button
            if (citations.isNotEmpty) ...[
              Container(height: 1, color: lightGray),
              InkWell(
                onTap: () {
                  setState(() {
                    _messages[index]['showCitations'] = !showCitations;
                  });
                },
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  decoration: BoxDecoration(
                    color: deepSlate.withAlpha(8),
                    borderRadius: showCitations
                        ? BorderRadius.zero
                        : const BorderRadius.only(
                            bottomLeft: Radius.circular(16),
                            bottomRight: Radius.circular(16),
                          ),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.description_outlined, color: deepSlate, size: 22),
                      const SizedBox(width: 12),
                      Text(
                        'View Official SEC Sources',
                        style: TextStyle(
                          fontSize: 16,
                          color: deepSlate,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const Spacer(),
                      AnimatedRotation(
                        turns: showCitations ? 0.5 : 0,
                        duration: const Duration(milliseconds: 200),
                        child: Icon(Icons.expand_more, color: deepSlate, size: 24),
                      ),
                    ],
                  ),
                ),
              ),
              // Expandable citations
              if (showCitations)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: offWhite,
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(16),
                      bottomRight: Radius.circular(16),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: citations.take(5).map((citation) {
                      return Container(
                        margin: const EdgeInsets.only(bottom: 16),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: cardWhite,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: lightGray),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: slateGray.withAlpha(15),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                'SEC SOURCE',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                  color: slateGray,
                                  letterSpacing: 0.5,
                                ),
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              citation.length > 300 ? '${citation.substring(0, 300)}...' : citation,
                              style: TextStyle(
                                fontSize: 15,
                                color: deepSlate,
                                height: 1.6,
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildLoadingIndicator() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
            decoration: BoxDecoration(
              color: cardWhite,
              borderRadius: BorderRadius.circular(30),
              border: Border.all(color: lightGray),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                SizedBox(
                  width: 22,
                  height: 22,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.5,
                    valueColor: AlwaysStoppedAnimation<Color>(accentBlue),
                  ),
                ),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Step ${_statusStep + 1} of ${_statusSteps.length}',
                      style: TextStyle(
                        color: slateGray,
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 4),
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 300),
                      child: Text(
                        _statusSteps[_statusStep],
                        key: ValueKey<int>(_statusStep),
                        style: TextStyle(
                          color: deepSlate,
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    if (_isDeepAnalysis) ...[
                      const SizedBox(height: 4),
                      Text(
                        'Performing deep cross-analysis (this may take up to 5 minutes)...',
                        style: TextStyle(
                          color: mediumGray,
                          fontSize: 13,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                    const SizedBox(height: 12),
                    SizedBox(
                      width: 200,
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(2),
                        child: LinearProgressIndicator(
                          value: _progressValue,
                          backgroundColor: lightGray,
                          valueColor: AlwaysStoppedAnimation<Color>(accentBlue),
                          minHeight: 4,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickFactsPanel() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            border: Border(bottom: BorderSide(color: lightGray)),
          ),
          child: Row(
            children: [
              Icon(
                _comparisonTickers.length >= 2 
                    ? Icons.compare_arrows 
                    : Icons.lightbulb_outline, 
                color: deepSlate, 
                size: 24,
              ),
              const SizedBox(width: 12),
              Text(
                _comparisonTickers.length >= 2 ? 'Comparison' : 'Quick Facts',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: deepSlate,
                ),
              ),
            ],
          ),
        ),
        // Content
        Expanded(
          child: _comparisonTickers.isEmpty
              ? _buildEmptyQuickFacts()
              : _comparisonTickers.length >= 2
                  ? _buildComparisonContent()
                  : _buildSingleCompanyContent(_comparisonTickers.first),
        ),
      ],
    );
  }

  Widget _buildEmptyQuickFacts() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.business_center_outlined, size: 64, color: lightGray),
            const SizedBox(height: 20),
            Text(
              'Company insights will\nappear here',
              style: TextStyle(
                fontSize: 16,
                color: mediumGray,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  String _formatNetIncome(int amount) {
    final billions = amount / 1000000000;
    return '\$${billions.toStringAsFixed(1)}B';
  }

  Widget _buildComparisonContent() {
    final ticker1 = _comparisonTickers[0];
    final ticker2 = _comparisonTickers[1];
    final facts1 = _companyQuickFacts[ticker1]!;
    final facts2 = _companyQuickFacts[ticker2]!;
    final income1 = facts1['netIncome2023'] as int;
    final income2 = facts2['netIncome2023'] as int;
    final leader = income1 >= income2 ? ticker1 : ticker2;

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _buildComparisonCard(ticker1, facts1, leader == ticker1),
        const SizedBox(height: 16),
        _buildComparisonCard(ticker2, facts2, leader == ticker2),
      ],
    );
  }

  Widget _buildComparisonCard(String ticker, Map<String, dynamic> facts, bool isLeader) {
    final netIncome = facts['netIncome2023'] as int;
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: cardWhite,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isLeader ? accentBlue : lightGray,
          width: isLeader ? 2 : 1,
        ),
        boxShadow: isLeader
            ? [BoxShadow(color: accentBlue.withAlpha(20), blurRadius: 12, spreadRadius: 2)]
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row with ticker and Leader badge
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: accentBlue,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  ticker,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                    letterSpacing: 1,
                  ),
                ),
              ),
              const Spacer(),
              if (isLeader)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: accentBlue.withAlpha(15),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: accentBlue),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.emoji_events, color: accentBlue, size: 14),
                      const SizedBox(width: 4),
                      Text(
                        'Leader',
                        style: TextStyle(
                          color: accentBlue,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),
          // Company name
          Text(
            facts['name'] as String,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: deepSlate,
            ),
          ),
          const SizedBox(height: 8),
          // Sector
          Row(
            children: [
              Icon(Icons.category_outlined, size: 16, color: slateGray),
              const SizedBox(width: 8),
              Text(
                facts['sector'] as String,
                style: TextStyle(fontSize: 14, color: slateGray),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Net Income
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isLeader ? accentBlue.withAlpha(10) : offWhite,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(Icons.attach_money, size: 20, color: isLeader ? accentBlue : slateGray),
                const SizedBox(width: 8),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Net Income (FY2023)',
                      style: TextStyle(
                        fontSize: 11,
                        color: slateGray,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    Text(
                      _formatNetIncome(netIncome),
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: isLeader ? accentBlue : deepSlate,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSingleCompanyContent(String ticker) {
    final facts = _companyQuickFacts[ticker]!;
    
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        // Company name header
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [accentBlue.withAlpha(15), accentBlue.withAlpha(5)],
            ),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: accentBlue.withAlpha(40)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: accentBlue,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      ticker,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        letterSpacing: 1,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'FY$_currentYear',
                    style: TextStyle(
                      color: slateGray,
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                facts['name'] as String,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: deepSlate,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        // Facts list
        _buildFactRow(Icons.category_outlined, 'Sector', facts['sector'] as String),
        _buildFactRow(Icons.business_outlined, 'Industry', facts['industry'] as String),
        _buildFactRow(Icons.attach_money, 'Net Income', _formatNetIncome(facts['netIncome2023'] as int)),
        _buildFactRow(Icons.person_outline, 'CEO', facts['ceo'] as String),
        _buildFactRow(Icons.location_on_outlined, 'Headquarters', facts['headquarters'] as String),
      ],
    );
  }

  Widget _buildFactRow(IconData icon, String label, String value) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: offWhite,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(icon, color: slateGray, size: 20),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 12,
                    color: mediumGray,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.5,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 15,
                    color: deepSlate,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputSection() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 20),
      decoration: BoxDecoration(
        color: cardWhite,
        border: Border(top: BorderSide(color: lightGray)),
      ),
      child: Container(
        height: 60,
        decoration: BoxDecoration(
          color: offWhite,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: lightGray, width: 1.5),
        ),
        child: Row(
          children: [
            // Search icon
            Padding(
              padding: const EdgeInsets.only(left: 16),
              child: Icon(Icons.search, color: slateGray, size: 26),
            ),
            // Text input
            Expanded(
              child: TextField(
                controller: _controller,
                style: TextStyle(
                  color: deepSlate,
                  fontSize: 18,
                ),
                decoration: InputDecoration(
                  hintText: 'Ask about Apple, Microsoft, Tesla, Google...',
                  hintStyle: TextStyle(
                    color: slateGray,
                    fontSize: 18,
                  ),
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 18,
                  ),
                ),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
            // Attached Analyze button
            Container(
              height: 60,
              decoration: BoxDecoration(
                color: accentBlue,
                borderRadius: const BorderRadius.only(
                  topRight: Radius.circular(11),
                  bottomRight: Radius.circular(11),
                ),
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: _sendMessage,
                  borderRadius: const BorderRadius.only(
                    topRight: Radius.circular(11),
                    bottomRight: Radius.circular(11),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: Row(
                      children: const [
                        Text(
                          'Analyze',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(width: 8),
                        Icon(Icons.arrow_forward, color: Colors.white, size: 20),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
