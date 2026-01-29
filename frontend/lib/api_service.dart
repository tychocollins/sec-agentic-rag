import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000';




  Future<Map<String, dynamic>> analyze(String userInput) async {
    final url = Uri.parse('$baseUrl/analyze');
    
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_input': userInput,
        }),
      ).timeout(const Duration(minutes: 5));


      if (response.statusCode == 200) {
        return jsonDecode(utf8.decode(response.bodyBytes));
      } else {
        throw Exception('Failed to analyze question: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error connecting to server: $e');
    }
  }

  Stream<Map<String, dynamic>> analyzeStream(String userInput) async* {
    final url = Uri.parse('$baseUrl/analyze');
    final client = http.Client();
    
    try {
      final request = http.Request('POST', url)
        ..headers['Content-Type'] = 'application/json'
        ..body = jsonEncode({'user_input': userInput});

      final response = await client.send(request).timeout(const Duration(minutes: 5));

      if (response.statusCode == 200) {
        final stream = response.stream
            .transform(utf8.decoder)
            .transform(const LineSplitter());

        await for (var line in stream) {
          if (line.startsWith('data: ')) {
            final data = line.substring(6).trim();
            if (data.isNotEmpty) {
              yield jsonDecode(data);
            }
          }
        }
      } else {
        throw Exception('Failed to analyze (Stream): ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error in stream connection: $e');
    } finally {
      client.close();
    }
  }
}
